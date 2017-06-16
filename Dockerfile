FROM python:3.6.1
MAINTAINER furion <_@furion.me>

# install talib
#RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
#RUN tar -xzf ta-lib-0.4.0-src.tar.gz
#WORKDIR /ta-lib
#RUN ls
#RUN ./configure
#RUN make
#RUN make install
#ENV LD_LIBRARY_PATH="/usr/local/lib:$LD_LIBRARY_PATH"

COPY .plotly/.credentials /root/.plotly/

COPY . /project_root
WORKDIR /project_root

ENV UNLOCK foo

RUN pip install -r requirements.txt

#RUN pip install TA-lib

# use old cufflinks instead
#RUN pip install --upgrade --no-deps --force-reinstall git+git://github.com/santosjorge/cufflinks.git@ef63fd24b08a082ff7ef6178754cacd57d719690
RUN pip install git+git://github.com/santosjorge/cufflinks.git@ef63fd24b08a082ff7ef6178754cacd57d719690

RUN jupyter nbconvert --to script Charts.ipynb
RUN jupyter nbconvert --to script ChartsLR.ipynb
RUN jupyter nbconvert --to script MarketCap.ipynb

RUN chmod +x run.sh
CMD "./run.sh"
