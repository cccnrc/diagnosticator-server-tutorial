### try to install a proper CA SSL certificate:

### instal certbot: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/SSL-on-amazon-linux-2.html#letsencrypt
sudo wget -r --no-parent -A 'epel-release-*.rpm' https://dl.fedoraproject.org/pub/epel/7/x86_64/Packages/e/
sudo rpm -Uvh dl.fedoraproject.org/pub/epel/7/x86_64/Packages/e/epel-release-*.rpm
sudo yum-config-manager --enable epel*
sudo yum repolist all

### change NGINX
sudo vim /etc/nginx/conf.d/diagnosticator.conf      ### add domain in server_name
sudo service nginx reload

### install CERTBOT
sudo yum install -y certbot python2-certbot-apache
sudo certbot


### IMPORTANT: before being able to have the certificate issued the certbot server
#               needs to communicate in HTTP with your domain. Thus you need to have
#               forwarding from diagnosticator.com to your machine IP address (A record in domain DNS)
#               and the NGINX must allow HTTP requests (stop automathic redirect to HTTPS)
#               CERTBOT creates a temporary ".well-known" DIR in the path you specified
#               and then looks for this DIR content from the HTTP request so you can configure
#               NGINX to automatically serve it (in HTTP) as for "static"
#       to renew just run: certbot renew

### create the DIR to automatically serve outside
mkdir /home/ec2-user/diagnosticator-server-AWS/letsencrypt-verification
### NGINX automatic HTTPS redirect needs to be stopped
sudo vim /etc/nginx/conf.d/diagnosticator.conf
sudo service nginx reload
### run certbot serving that DIR
sudo certbot certonly --webroot -w /home/ec2-user/diagnosticator-server-AWS/letsencrypt-verification -d diagnosticator.com -d www.diagnosticator.com
### you get your certificates in:
/etc/letsencrypt/live/diagnosticator.com/fullchain.pem
/etc/letsencrypt/live/diagnosticator.com/privkey.pem
### just add it to NGINX and restore HTTPS redirect
sudo vim /etc/nginx/conf.d/diagnosticator.conf
sudo service nginx reload




























###ENDc