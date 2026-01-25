/*
Вариант 4

Рощин Филипп Андреевич

Описание предметной области
Описание хранящихся на складе товаров. Включает в себя: описание помещений, описание стеллажей,
описание клиентов, описание товаров, хранящихся на стеллажах. Описание помещения состоит из: названия,
полезного объёма, температурных и влажностных условий. Описание стеллажа состоит из: номера, указания
помещения, в котором стеллаж находится, количества мест для хранения в стеллаже, высоты, ширины и длины одного места,
максимальной суммарной нагрузки. Описание клиента состоит из: названия юридического лица и банковских реквизитов в виде большого текста.
Описание товара, хранящегося на стеллажах, состоит из: высоты, ширины, длины, веса, даты поступления, номера договора,
указания, от какого клиента поступил, даты окончания договора, температурных и влажностных условий хранения, указания стеллажа,
и позиции размещения на нём, представляемой в виде целого номера.

На одном стеллаже могут храниться товары разных клиентов.

Вариант 4
Выберите номера стеллажей, а также объём одного места и суммарный объём всех мест на каждом из них.
Выберите названия юр. лиц всех клиентов и количество их товаров на стеллажах.
*/

-- Таблица клиентов
CREATE TABLE clients (
    id INTEGER PRIMARY KEY,
    name_of_a_legal_entity TEXT NOT NULL,
    bank_details TEXT NOT NULL
);

-- Таблица помещений
CREATE TABLE rooms (
    id INTEGER PRIMARY KEY,
    room_name TEXT NOT NULL,
    useful_volume REAL NOT NULL,
    min_temperature REAL,
    max_temperature REAL,
    min_humidity REAL,
    max_humidity REAL
);

-- Таблица стеллажей
CREATE TABLE racks (
    id INTEGER PRIMARY KEY,
    room_id INTEGER NOT NULL,
    rack_number TEXT NOT NULL,
    storage_spaces_count INTEGER NOT NULL,
    space_height REAL NOT NULL,
    space_width REAL NOT NULL,
    space_length REAL NOT NULL,
    max_total_load REAL NOT NULL,
    FOREIGN KEY (room_id) REFERENCES rooms(id),
    UNIQUE (rack_number, room_id)
);

-- Таблица товаров
CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    height REAL NOT NULL,
    width REAL NOT NULL,
    length REAL NOT NULL,
    weight REAL NOT NULL,
    admission_date TEXT NOT NULL,
    contract_number TEXT NOT NULL,
    client_id INTEGER NOT NULL,
    contract_expiration_date TEXT NOT NULL,
    min_temperature REAL,
    max_temperature REAL,
    min_humidity REAL,
    max_humidity REAL,
    rack_id INTEGER NOT NULL,
    position_number INTEGER NOT NULL,
    FOREIGN KEY (client_id) REFERENCES clients(id),
    FOREIGN KEY (rack_id) REFERENCES racks(id),
    UNIQUE (rack_id, position_number)
);

-- Заполнение таблицы клиентов
INSERT INTO clients (id, name_of_a_legal_entity, bank_details) VALUES
    (1, 'ООО "Ромашка"', 'БИК 044525225, р/с 40702810200000012345 в АО "Альфа-Банк", к/с 30101810200000000593'),
    (2, 'АО "Технопром"', 'БИК 044525555, р/с 40702810400000056789 в ПАО "Сбербанк", к/с 30101810400000000225'),
    (3, 'ИП Сидоров А.В.', 'БИК 044525999, р/с 40802810000000123456 в ПАО "ВТБ", к/с 30101810700000000123'),
    (4, 'ООО "ГлобалЛоджистик"', 'БИК 044525888, р/с 40702810500000098765 в АО "Тинькофф Банк", к/с 30101810100000000876'),
    (5, 'ЗАО "АгроПродукт"', 'БИК 044525777, р/с 40702810600000054321 в ПАО "Открытие", к/с 30101810500000000765');

-- Заполнение таблицы помещений
INSERT INTO rooms (id, room_name, useful_volume, min_temperature, max_temperature, min_humidity, max_humidity) VALUES
    (1, 'Холодильная камера №1', 150.5, -5.0, 5.0, 40.0, 70.0),
    (2, 'Основной складской зал', 500.0, 15.0, 25.0, 30.0, 60.0),
    (3, 'Холодильная камера №2', 120.0, 2.0, 8.0, 45.0, 75.0),
    (4, 'Сухое хранение', 300.0, 18.0, 22.0, 20.0, 40.0),
    (5, 'Универсальный склад', 400.0, 10.0, 20.0, 35.0, 65.0);

-- Заполнение таблицы стеллажей
INSERT INTO racks (id, room_id, rack_number, storage_spaces_count, space_height, space_width, space_length, max_total_load) VALUES
    (1, 1, 'ХК1-А01', 10, 2.0, 1.5, 2.0, 5000.0),
    (2, 2, 'ОСЗ-Б02', 15, 2.5, 2.0, 2.5, 8000.0),
    (3, 3, 'ХК2-В03', 8, 1.8, 1.2, 1.8, 3000.0),
    (4, 4, 'СХ-Г04', 12, 2.2, 1.8, 2.2, 6000.0),
    (5, 5, 'УС-Д05', 20, 2.0, 1.5, 2.0, 7000.0),
    (6, 2, 'ОСЗ-Б03', 10, 2.0, 1.5, 2.0, 4500.0);

-- Заполнение таблицы товаров
INSERT INTO products (id, height, width, length, weight, admission_date, contract_number, client_id, contract_expiration_date, min_temperature, max_temperature, min_humidity, max_humidity, rack_id, position_number) VALUES
    (1, 1.8, 1.4, 1.9, 450.5, '2024-01-15', 'ДГ-2024-001', 1, '2024-12-31', -2.0, 4.0, 45.0, 65.0, 1, 1),
    (2, 2.4, 1.9, 2.4, 780.2, '2024-01-20', 'ДГ-2024-002', 2, '2024-12-31', 16.0, 22.0, 35.0, 55.0, 2, 1),
    (3, 1.7, 1.1, 1.7, 320.8, '2024-02-01', 'ДГ-2024-003', 3, '2024-11-30', 3.0, 7.0, 48.0, 70.0, 3, 1),
    (4, 2.1, 1.7, 2.1, 550.0, '2024-02-10', 'ДГ-2024-004', 4, '2025-01-15', 19.0, 21.0, 25.0, 38.0, 4, 1),
    (5, 1.9, 1.4, 1.9, 480.3, '2024-02-15', 'ДГ-2024-005', 5, '2024-10-31', 12.0, 18.0, 40.0, 60.0, 5, 1),
    (6, 1.6, 1.3, 1.6, 380.7, '2024-03-01', 'ДГ-2024-006', 1, '2024-12-31', -3.0, 3.0, 50.0, 68.0, 1, 2),
    (7, 2.3, 1.8, 2.3, 720.1, '2024-03-05', 'ДГ-2024-007', 2, '2024-12-31', 17.0, 23.0, 32.0, 58.0, 2, 2),
    (8, 1.5, 1.0, 1.5, 290.4, '2024-03-10', 'ДГ-2024-008', 3, '2024-11-30', 4.0, 6.0, 52.0, 72.0, 3, 2),
    (9, 2.0, 1.6, 2.0, 510.9, '2024-03-15', 'ДГ-2024-009', 4, '2025-01-15', 18.0, 20.0, 28.0, 42.0, 4, 2),
    (10, 1.8, 1.3, 1.8, 420.6, '2024-03-20', 'ДГ-2024-010', 5, '2024-10-31', 13.0, 17.0, 45.0, 62.0, 5, 2),
    (11, 1.7, 1.2, 1.7, 350.2, '2024-04-01', 'ДГ-2024-011', 1, '2024-12-31', -1.0, 5.0, 47.0, 67.0, 6, 1),
    (12, 2.2, 1.7, 2.2, 680.4, '2024-04-05', 'ДГ-2024-012', 2, '2024-12-31', 15.0, 21.0, 38.0, 57.0, 6, 2);


-- 1. Выбор номеров стеллажей, объёма одного места и суммарного объёма всех мест на каждом из них
SELECT 
    r.rack_number AS "Номер стеллажа",
    (r.space_height * r.space_width * r.space_length) AS "Объём одного места (м³)",
    (r.space_height * r.space_width * r.space_length * r.storage_spaces_count) AS "Суммарный объём всех мест (м³)"
FROM racks r
ORDER BY r.rack_number;

-- 2. Выбор названий юр. лиц всех клиентов и количества их товаров на стеллажах
SELECT 
    c.name_of_a_legal_entity AS "Название юр. лица",
    COUNT(p.id) AS "Количество товаров"
FROM clients c
LEFT JOIN products p ON c.id = p.client_id
GROUP BY c.id, c.name_of_a_legal_entity
ORDER BY COUNT(p.id) DESC;















-- Таблица помещений
CREATE TABLE rooms (
    id INTEGER PRIMARY KEY,
    room_name TEXT NOT NULL,
    useful_volume REAL NOT NULL,
    min_temperature REAL,
    max_temperature REAL,
    min_humidity REAL,
    max_humidity REAL
);

-- Таблица стеллажей
CREATE TABLE racks (
    id INTEGER PRIMARY KEY,
    room_id INTEGER NOT NULL,
    rack_number TEXT NOT NULL,
    storage_spaces_count INTEGER NOT NULL,
    space_height REAL NOT NULL,
    space_width REAL NOT NULL,
    space_length REAL NOT NULL,
    max_total_load REAL NOT NULL,
    FOREIGN KEY (room_id) REFERENCES rooms(id),
    UNIQUE (rack_number, room_id)
);