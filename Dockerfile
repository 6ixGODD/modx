FROM ubuntu:latest
LABEL authors="BC"

ENTRYPOINT ["top", "-b"]