USE fourthcoffee;

CREATE TABLE fourthcoffee.products (
    ProductID int NOT NULL AUTO_INCREMENT,
    Name text,
    Price double,
    Stock int,
    PRIMARY KEY (ProductID)
);

INSERT INTO fourthcoffee.products (Name, Price, Stock)
VALUES ('Red apple', 4.8, 10000),
       ('Banana', 2, 10000),
       ('Avocado', 11, 10000),
       ('Bread', 22, 10000),
       ('Milk', 2, 10000),
       ('Orange juice', 2, 10000),
       ('Chips', 1.2, 10000),
       ('Red Bell Pepper', 6, 10000),
       ('Lettuce', 7, 10000);
