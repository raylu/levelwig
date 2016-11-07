import os
from os import path
import shutil

import db

levelwig_dir = path.normpath(path.dirname(path.abspath(__file__)))
public_dir = path.join(levelwig_dir, 'public')

def generate(app):
	try:
		shutil.rmtree(public_dir)
	except FileNotFoundError as e:
		if e.filename != public_dir:
			raise
	os.mkdir(public_dir)

	posts = db.iter_posts(allowed_flags=0)
	stream = app.template_engine.stream('root.jinja2', {'posts': posts})
	with open(path.join(public_dir, 'index.html'), 'wb') as f:
		for buf in stream:
			f.write(buf)

	for post in db.iter_posts(allowed_flags=db.PostFlag.draft):
		stream = app.template_engine.stream('post.jinja2', {'post': post})
		with open(path.join(public_dir, '%d.html' % post.id), 'wb') as f:
			for buf in stream:
				f.write(buf)
