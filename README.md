# levelwig
generate static blogs with a web interface

built on [leveldb](http://leveldb.org/) and [pigwig](https://github.com/raylu/pigwig)

## dev setup:
	git submodule update --init
	sudo apt install libffi-dev libleveldb-dev
	pip3 install -r requirements.txt
	./levelwig dev 8000

## prod setup:
	pip3 install eventlet
	./levelwig gen
	./levelwig prod 8000

## webserver configuration
### nginx:
	server {
		server_name levelwig;
		listen 80;
		listen [::]:80;
		add_header X-Frame-Options DENY;
		add_header X-Content-Type-Options nosniff;
		add_header Content-Security-Policy "default-src none; style-src 'self'; img-src https: 'self'";
		add_header X-Xss-Protection "1; mode=block";
		charset utf-8;
		index index.html;
		location / {
			root /home/raylu/src/levelwig/public;
			rewrite ^/post/([0-9]+) /$1.html;
		}
		location /admin {
			include proxy_params;
			proxy_pass http://127.0.0.1:8000;
		}
	}

### lighttpd:
	$HTTP["host"] == "levelwig" {
		server.document-root = "/home/raylu/src/levelwig/public"
		url.rewrite-once = (
			"^/post/([0-9]+)" => "/$1.html"
		)
		$HTTP["url"] =~ "^/admin" {
			proxy.server = ("" => (("host" => "127.0.0.1", "port" => 8000)))
		}
	}
