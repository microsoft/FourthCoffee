use fourthcoffeedb;
 CREATE TABLE fourthcoffeedb.products (
    id int NOT NULL AUTO_INCREMENT,
    Name text,
    Price double,
    Stock int,
    photopath text,
    PRIMARY KEY (id)
);   

INSERT INTO fourthcoffeedb.products (Name, Price, Stock, photopath)
VALUES ('Regular Coffee', 2.5, 10000, "static/img/product1.jpg"),
       ('Espresso', 3.25, 10000, "static/img/product2.jpg"),
       ('Hot Chocolate', 3.75, 10000, "static/img/product3.jpg"),
       ('Cafe Mocha', 3.00, 10000, "static/img/product4.jpg"),
       ('Black Tea', 1.75, 10000, "static/img/product5.jpg"),
       ('Cafe Latte', 4, 10000, "static/img/product6.jpg"),
       ('Green Tea', 2.0, 10000, "static/img/product7.jpg"),
       ('Double Espresso', 3.5, 10000, "static/img/product8.jpg"),
       ('Go Fourth Sample', 7, 10000, "static/img/product9.jpg");
       
    