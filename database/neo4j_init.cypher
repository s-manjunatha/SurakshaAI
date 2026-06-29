// SurakshAI Neo4j Graph Schema Initialization

// Constraints
CREATE CONSTRAINT criminal_id IF NOT EXISTS FOR (c:Criminal) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT victim_id IF NOT EXISTS FOR (v:Victim) REQUIRE v.id IS UNIQUE;
CREATE CONSTRAINT fir_id IF NOT EXISTS FOR (f:FIR) REQUIRE f.id IS UNIQUE;
CREATE CONSTRAINT phone_id IF NOT EXISTS FOR (p:Phone) REQUIRE p.id IS UNIQUE;
CREATE CONSTRAINT vehicle_id IF NOT EXISTS FOR (v:Vehicle) REQUIRE v.id IS UNIQUE;
CREATE CONSTRAINT bank_id IF NOT EXISTS FOR (b:BankAccount) REQUIRE b.id IS UNIQUE;
CREATE CONSTRAINT location_id IF NOT EXISTS FOR (l:Location) REQUIRE l.id IS UNIQUE;

// Indexes
CREATE INDEX criminal_name IF NOT EXISTS FOR (c:Criminal) ON (c.name);
CREATE INDEX fir_number IF NOT EXISTS FOR (f:FIR) ON (f.fir_number);
CREATE INDEX crime_type IF NOT EXISTS FOR (f:FIR) ON (f.crime_type);

// Relationship types:
// (Criminal)-[:COMMITTED]->(FIR)
// (Victim)-[:VICTIM_OF]->(FIR)
// (Criminal)-[:USED]->(Phone)
// (Criminal)-[:OWNS]->(Vehicle)
// (Criminal)-[:OWNS]->(BankAccount)
// (BankAccount)-[:TRANSFERRED {amount, date}]->(BankAccount)
// (FIR)-[:OCCURRED_AT]->(Location)
// (Criminal)-[:CONNECTED_TO {strength, type}]->(Criminal)
