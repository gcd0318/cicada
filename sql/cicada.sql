create database cicada;

CREATE USER cicada@'localhost' IDENTIFIED BY 'cicada';

grant all on cicada.* to cicada@localhost;

flush privileges;
