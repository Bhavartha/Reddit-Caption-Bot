#!/usr/bin/env python
# -*- coding: utf-8 -*-

# importing required libraries

from PIL import Image , ImageFont , ImageDraw
import requests
import os

imgbb_key = os.environ.get('imgbb_key')
reddit_client_id = os.environ.get('reddit_client_id')
reddit_client_secret = os.environ.get('reddit_client_secret')
reddit_username = os.environ.get('reddit_username')
reddit_password = os.environ.get('reddit_password')

def combine(image1,image2):
    output = Image.new('RGB', (image1.width, image1.height + image2.height)) # Creating new blank image
    output.paste(image1, (0, 0)) # Copy-Paste first image at top
    output.paste(image2, (0, image1.height)) # Copy-Paste second image just below the first image
    return output

# Line splitting logic based on word size and image width

def line_split(text, font, max_width):
    lines = []
    # If the width of the text is smaller than image width
    # we don't need to split it, just add it to the lines array
    # and return
    if font.getsize(text)[0] <= max_width:
        lines.append(text)
    else:
        # split the line by spaces to get words
        words = text.split(' ')
        i = 0
        # append every word to a line while its width is shorter than image width
        while i < len(words):
            line = ''
            while i < len(words) and font.getsize(line + words[i])[0] <= max_width:
                line = line + words[i] + " "
                i += 1
            if not line:
                line = words[i]
                i += 1
            # when the line gets longer than the max width do not append the word,
            # add the line to the lines array
            lines.append(line)
    return lines

def make_gif(gif_path,text,padx=10,pady=10):

    # open the image file
    img = Image.open(requests.get(gif_path, stream=True).raw)
    # Calculate width of top-caption image
    width = img.size[0]
    font = ImageFont.truetype("Roboto-Medium.ttf",width//13)
    # Getting the line-splits
    max_width = width-(2*padx)
    lines = line_split(text=text,font=font,max_width=max_width)

    # Calculate height of top-caption image (height of text * no. of lines + padding)
    height = len(lines)*font.getsize(text)[1]+2*pady

    caption_image = Image.new('RGB', (width, height), 'white')
    caption_writer = ImageDraw.Draw(caption_image)
    y_pos = pady
    for line in lines:
        caption_writer.text((padx,y_pos), line , fill='black',font=font) # Write line of text onto image
        y_pos+= font.getsize(line)[1] # Move to next line

    op_gif = []
    duration=[]
    try:
        while True:
            img.seek(img.tell()+1) # Seek next frame
            duration.append(img.info['duration']) 
            new_frame= combine(caption_image,img)# Get combined image
            op_gif.append(new_frame) # Append frame to new gif
    except EOFError:
        pass # end of sequence
    
    # Saving the new gif
    op_gif[0].save("/app/tmp/output.gif",save_all=True, append_images=op_gif[1:], loop=0,duration=duration)
    
    
# Upload image to imagebb

url = f"https://api.imgbb.com/1/upload"

import base64
def uploadgif():
    with open("/app/tmp/output.gif", "rb") as file:
        payload = {
            "key": imgbb_key,
            "image": base64.b64encode(file.read()),
        }
        res = requests.post(url, payload)

    return res.json()['data']['url']

import praw

autoreply = """

This meme was auto-generated by a bot.

Usage: 

u/gifcaptionbot

<caption>

<gif-link>

"""

reddit = praw.Reddit(user_agent="Gif caption by Bhavartha",
                     client_id=reddit_client_id, client_secret=reddit_client_secret,
                     username=reddit_username, password=reddit_password)

for comment in reddit.inbox.stream(skip_existing=True):
        try:
#             comment.reply("Makin...")
            lst = [_.strip() for _ in comment.body.split('\n') if _.strip() not in ['','&#x200B;']]
#             print(lst)
            
            index = lst.index("[u/gifcaptionbot](https://www.reddit.com/u/gifcaptionbot/)")
            gif_path = str(lst[index+2])
            gif_path = gif_path[gif_path.index('(')+1:gif_path.index(')')]
#             comment.reply(gif_path)
            
            text=str(lst[index+1])
#             comment.reply(text)
            
            make_gif(gif_path,text)
            link = uploadgif()
#             print(link)
            comment.reply(link+autoreply)
        except Exception as e:
            print(e)
