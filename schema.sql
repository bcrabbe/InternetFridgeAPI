CREATE TABLE IF NOT EXISTS borrowingMessages (
   ID INTEGER PRIMARY KEY AUTOINCREMENT,
   message TEXT
);

INSERT INTO borrowingMessages(message) VALUES('none specified'),
('you can help yourself'),('please do not use'),('use but please replace'),
('use but do not finish');

CREATE TABLE IF NOT EXISTS users (
   ID INTEGER PRIMARY KEY AUTOINCREMENT,
   name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS storageRequirements (
   ID INTEGER PRIMARY KEY AUTOINCREMENT,
   message TEXT
);

INSERT INTO storageRequirements(message) VALUES('none specified'),
('store in a cool dry place'),('refrigerate'),('freeze');

CREATE TABLE IF NOT EXISTS products (
    EAN INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    daysToUseByAfterOpening INT,
    storageRequirementsID INT,
    averageStock REAL DEFAULT 0,
    FOREIGN KEY(storageRequirementsID) REFERENCES storageRequirements(ID)
);



CREATE TABLE IF NOT EXISTS inventory (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    dateAdded TEXT,
    useByDate TEXT,
    dateOpened TEXT,
    productEAN INT,
    ownerID INT,
    borrowingMessageID INT DEFAULT '1',
    FOREIGN KEY(productEAN) REFERENCES EANs(EAN),
    FOREIGN KEY(ownerID) REFERENCES users(ID),
    FOREIGN KEY(borrowingMessageID) REFERENCES borrowingMessages(ID)
);

CREATE TABLE IF NOT EXISTS usedItems (
   ID INTEGER PRIMARY KEY,
   dateAdded TEXT,
   dateFinished TEXT,
   productEAN INT,
   ownerID INT,
   FOREIGN KEY(productEAN) REFERENCES EANs(EAN),
   FOREIGN KEY(ownerID) REFERENCES users(ID)
);

CREATE TABLE IF NOT EXISTS recipes (
   ID INTEGER PRIMARY KEY AUTOINCREMENT,
   name TEXT NOT NULL,
   instructions TEXT,
   serves INT
);

CREATE TABLE IF NOT EXISTS recipesIngredients (
   ID INTEGER PRIMARY KEY AUTOINCREMENT,
   recipeID INT,
   ingredientEAN INT,
   ammount REAL,
   ammountUnits TEXT,
   FOREIGN KEY(recipeID) REFERENCES recipes(ID),
   FOREIGN KEY(ingredientEAN) REFERENCES EANs(EAN)
);
