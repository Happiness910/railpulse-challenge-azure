CREATE TABLE stations (
    station_id INT IDENTITY(1,1) PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE vehicles (
    vehicle_id INT IDENTITY(1,1) PRIMARY KEY,
    name VARCHAR(100)
);

CREATE TABLE liveboard_records (
    record_id INT IDENTITY(1,1) PRIMARY KEY,
    station_id INT NOT NULL,
    vehicle_id INT,
    destination VARCHAR(100),
    departure_time DATETIME,
    delay_minutes INT,
    platform VARCHAR(20),
    created_at DATETIME DEFAULT GETDATE(),

    FOREIGN KEY (station_id)
    REFERENCES stations(station_id),

    FOREIGN KEY (vehicle_id)
    REFERENCES vehicles(vehicle_id)
);