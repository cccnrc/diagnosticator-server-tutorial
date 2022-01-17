### try to install a proper CA SSL certificate:

### instal certbot: https://www.digitalocean.com/community/tutorials/how-to-secure-nginx-with-let-s-encrypt-on-ubuntu-20-04
sudo apt install certbot python3-certbot-nginx

### change NGINX
sudo vim /etc/nginx/conf.d/diagnosticator.conf      ### add domain in server_name
sudo service nginx reload

### install CERTBOT
sudo certbot


### IMPORTANT: before being able to have the certificate issued the certbot server
#               needs to communicate in HTTP with your domain. Thus you need to have
#               forwarding from diagnosticator.com to your machine IP address (A record in domain DNS)
#               and the NGINX must allow HTTP requests (stop automathic redirect to HTTPS)
#               CERTBOT creates a temporary ".well-known" DIR in the path you specified
#               and then looks for this DIR content from the HTTP request so you can configure
#               NGINX to automatically serve it (in HTTP) as for "static"
#       to renew just run: certbot renew

### you get your certificates in:
/etc/letsencrypt/live/diagnosticator-tutorial.com/fullchain.pem
/etc/letsencrypt/live/diagnosticator-tutorial.com/privkey.pem
### just add it to NGINX and restore HTTPS redirect
sudo vim /etc/nginx/conf.d/diagnosticator.conf
sudo service nginx reload




























###ENDc
