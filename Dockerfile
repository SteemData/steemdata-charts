FROM python:3.5.3
MAINTAINER furion <_@furion.me>

COPY .plotly/.credentials /root/.plotly/

COPY . /project_root
WORKDIR /project_root

ENV UNLOCK foo

RUN pip install -r requirements.txt

RUN chmod +x run.sh

# CMD ["runipy", "Charts.ipynb"]
CMD ["python", "charts.py"]
#ENTRYPOINT ./run.sh
