FROM python:3.7.5-slim
WORKDIR /usr/src/app
RUN python -m pip install \
    parse
COPY configurator.py .
COPY Vagrantfile_template .
CMD ["python", "configurator.py"]