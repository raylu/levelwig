import atexit
from enum import IntEnum
from os import path
import struct

from passlib.apps import custom_app_context
import plyvel

levelwig_dir = path.normpath(path.dirname(path.abspath(__file__)))
db_path = path.join(levelwig_dir, 'database')
db = plyvel.DB(db_path, create_if_missing=True)
users_db = db.prefixed_db(b'user-')
posts_db = db.prefixed_db(b'post-')

class PostFlag(IntEnum):
	deleted = 0x00000001
	draft = 0x00000002

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
	post_id = _pad_num(post_count + 1)
	flags = PostFlag.draft
	post_data = struct.pack('I', flags)
	post_data += username.encode('utf-8') + b'\0'
	post_data += title.encode('utf-8') + b'\0'
	post_data += body.encode('utf-8')
	with posts_db.write_batch() as batch:
		batch.put(post_id, post_data)
		batch.put(b'count', post_id)

def iter_posts(allowed_flags):
	post_count = posts_db.get(b'count', b'000000')
	with posts_db.iterator(stop=post_count, include_stop=True) as it:
		for post_id, post in it:
			flags = struct.unpack('I', post[:4])[0]
			if flags & allowed_flags != flags:
				continue
			username, title, body = post[4:].split(b'\0')
			yield flags, post_id, username.decode('utf-8'), title.decode('utf-8'), body.decode('utf-8')

def _pad_num(n):
	''' 5 -> b'000005' '''
	encoded = str(n).encode()
	buf = bytearray(b'000000')
	buf[-len(encoded):] = encoded
	return bytes(buf)

def close():
	db.close()
atexit.register(close)
