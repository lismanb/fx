FROM alpine:3.8
EXPOSE 5000
VOLUME /usr/src/app
WORKDIR /usr/src/app
RUN apk add --no-cache \
        uwsgi-python3 \
        python3 \
        mariadb-dev
RUN apk add --no-cache --virtual .build-deps \
		coreutils \
		gcc \
		make \
		python3-dev \
		musl-dev
COPY . .
RUN pip3 install --no-cache-dir -r requirements.txt
CMD flask init-db && uwsgi --socket 0.0.0.0:5000 --uid uwsgi --plugins python3 --protocol uwsgi --wsgi fx.wsgi