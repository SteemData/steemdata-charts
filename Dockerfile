FROM python:3.6.0
MAINTAINER furion <_@furion.me>

COPY .plotly/.credentials /root/.plotly/

COPY . /project_root
WORKDIR /project_root

ENV UNLOCK foo

RUN pip install -r requirements.txt

RUN pip install --upgrade --force-reinstall git+git://github.com/xeroc/piston@b912147475550ad1031b54d412dac44910b2a6a1
RUN pip install --upgrade --force-reinstall git+git://github.com/xeroc/python-steem@93a77344546fef584070c45de9a5bfd0e9d0f4ac
RUN pip install --upgrade --force-reinstall git+git://github.com/xeroc/python-graphenelib@76b39e52e4284425b43eb35785be575aaa82f495

# use local node
RUN piston set node ws://88.99.98.236:8090

# CMD ["runipy", "Charts.ipynb"]
CMD ["python", "__main__.py"]
