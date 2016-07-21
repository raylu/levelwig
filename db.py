import atexit
from enum import IntEnum
import os
from os import path
import struct

from passlib.apps import custom_app_context
import plyvel

levelwig_dir = path.normpath(path.dirname(path.abspath(__file__)))
db_path = path.join(levelwig_dir, 'database')
db = plyvel.DB(db_path, create_if_missing=True)
users_db = db.prefixed_db(b'user-')
posts_db = db.prefixed_db(b'post-')

def has_users():
	with users_db.iterator() as it:
		try:
			next(it)
		except StopIteration:
			return False
		return True

def create_user(username, password):
	hashed = custom_app_context.encrypt(password)
	users_db.put(username.encode('utf-8'), hashed.encode())

def check_login(username, password):
	hashed = users_db.get(username.encode('utf-8'))
	if hashed is None:
		return False
	return custom_app_context.verify(password, hashed)

def create_post(username, title, body):
	post_count = int(posts_db.get(b'count', 0))
	post = Post(post_count + 1, PostFlag.draft, username, title, body)
	with posts_db.write_batch() as batch:
		post_id = post.save(batch)
		batch.put(b'count', post_id)

def update_post(post_id, title, body):
	post_id = _pad_num(post_id)
	post = _parse_post(post_id, posts_db.get(post_id), PostFlag.draft)
	post.title = title
	post.body = body
	post.save()

def toggle_post_flag(post_id, flag, status):
	post_id = _pad_num(post_id)
	post = posts_db.get(post_id)
	flags = struct.unpack('I', post[:4])[0]
	if status:
		flags |= flag
	else:
		flags &= ~flag
	post_data = struct.pack('I', flags) + post[4:]
	posts_db.put(post_id, post_data)

def get_post(post_id, allowed_flags):
	post = posts_db.get(_pad_num(post_id))
	if post is not None:
		return _parse_post(post_id, post, allowed_flags)

def iter_posts(allowed_flags):
	post_count = posts_db.get(b'count', b'000000')
	with posts_db.iterator(stop=post_count, include_stop=True) as it:
		for post_id, post in it:
			parsed = _parse_post(post_id, post, allowed_flags)
			if parsed is None:
				continue
			yield parsed

def cookie_secret():
	cs = db.get(b'cookie_secret')
	if cs is None:
		cs = os.urandom(16)
		db.put(b'cookie_secret', cs)
	return cs

def _pad_num(n):
	''' 5 -> b'000005' '''
	encoded = str(n).encode()
	buf = bytearray(b'000000')
	buf[-len(encoded):] = encoded
	return bytes(buf)

def _parse_post(post_id, post, allowed_flags):
	flags = struct.unpack('I', post[:4])[0]
	if flags & allowed_flags != flags:
		return None
	username, title, body = post[4:].split(b'\0')
	username = username.decode('utf-8')
	title = title.decode('utf-8')
	body = body.decode('utf-8')
	return Post(post_id, flags, username, title, body)

class PostFlag(IntEnum):
	deleted = 0x00000001
	draft = 0x00000002

class Post:
	def __init__(self, post_id, flags, username, title, body):
		self.id = int(post_id)
		for name, bit in PostFlag.__members__.items():
			value = flags & bit == bit
			setattr(self, name, value)
		self.username = username
		self.title = title
		self.body = body

	def save(self, batch=None):
		post_id = _pad_num(self.id)
		flags = 0
		for name, bit in PostFlag.__members__.items():
			if getattr(self, name):
				flags |= bit
		post_data = struct.pack('I', flags)
		post_data += self.username.encode('utf-8') + b'\0'
		post_data += self.title.encode('utf-8') + b'\0'
		post_data += self.body.encode('utf-8')
		writer = batch
		if writer is None:
			writer = posts_db
		writer.put(post_id, post_data)
		return post_id

def close():
	db.close()
atexit.register(close)
