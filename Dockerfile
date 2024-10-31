FROM python:3.9

RUN mkdir -p /var/www/
WORKDIR /var/www/

COPY ./main.py /var/www/
COPY ./forms.py /var/www/
COPY ./requirements.txt /var/www/
ADD static /var/www/static
ADD templates /var/www/templates
#COPY ./gunicorn_config.py /var/www/

RUN pip install --no-cache-dir -r requirements.txt
#RUN export FLASK_ENV=production

#CMD gunicorn --gunicorn_config.py --worker-tmp-dir /dev/shm main:app
#CMD ["gunicorn","--gunicorn_config.py","--worker-tmp-dir","/dev/shm main:app"]
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "main:app"]

#EXPOSE 8080
#ENV TZ Europe/Kiev
#CMD ["python","app.py"]
