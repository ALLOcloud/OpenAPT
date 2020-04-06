FROM debian:buster

RUN apt-get update && \
  apt-get install -y --no-install-recommends gnupg && \
  apt-get clean

RUN echo 'deb http://repo.aptly.info/ squeeze main' > /etc/apt/sources.list.d/aptly.list && \
  apt-key adv --keyserver pool.sks-keyservers.net --recv-keys ED75B5A4483DA07C && \
  apt-get update && \
  apt-get install -y --no-install-recommends ca-certificates aptly && \
  apt-get clean

ADD aptly.conf /etc/aptly.conf

RUN mkdir debian
COPY debian/control debian
RUN apt-get install -y --no-install-recommends devscripts equivs sudo && \
  mk-build-deps -i -r -t 'apt-get -y --no-install-recommends' && \
  apt-get clean

RUN adduser --disabled-password --gecos '' docker && \
  echo "docker ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

USER docker
RUN gpg --no-default-keyring --keyring /usr/share/keyrings/debian-archive-keyring.gpg --export | gpg --no-default-keyring --keyring trustedkeys.gpg --import
