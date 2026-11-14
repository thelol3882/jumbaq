# Included by the /api/ locations of jumbaq.conf. Not *.conf, so nginx does not load it
# on its own from conf.d.
proxy_http_version 1.1;
proxy_set_header Connection "";
proxy_set_header Host $host;
proxy_set_header X-Request-ID $req_id;
# $remote_addr is the client IP from CF-Connecting-IP (see 00-cloudflare.conf). Set, not
# appended: an X-Forwarded-For sent by the client must not reach the API.
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $remote_addr;
proxy_set_header X-Forwarded-Proto https;
proxy_read_timeout 30s;
