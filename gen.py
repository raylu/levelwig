import os
from os import path

import db

levelwig_dir = path.normpath(path.dirname(path.abspath(__file__)))
public_dir = path.join(levelwig_dir, 'public')

def generate(app):
	try:
		os.mkdir(public_dir)
	except FileExistsError:
		pass

	posts = db.iter_posts(allowed_flags=0)
	stream = app.template_engine.stream('root.jinja2', {'posts': posts})
	with open(path.join(public_dir, 'index.html'), 'wb') as f:
		for buf in stream:
			f.write(buf)

	for post in db.iter_posts(allowed_flags=db.PostFlag.draft):
		post_id, flags, username, title, body = post
		stream = app.template_engine.stream('post.jinja2', {
			'flags': flags, 'username': username, 'title': title, 'body': body,
		})
		with open(path.join(public_dir, '%d.html' % post_id), 'wb') as f:
			for buf in stream:
				f.write(buf)
