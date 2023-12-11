FROM python:3.9-bullseye

RUN  pip install --upgrade pip && \
                pip install pandas \
                requests \
                boto3 \
                beautifulsoup4 \
                pyarrow \
                python-dotenv \
                pytest --target=/usr/local/lib/python3.9/dist-packages && \
                export PATH=$PATH:/usr/local/lib/python3.9/dist-packages

RUN mkdir -p /workspaces/app/  
COPY /src /workspaces/app 
WORKDIR /workspaces/app
              
ENV PYTHONPATH=/usr/local/bin/python

CMD ["python"]