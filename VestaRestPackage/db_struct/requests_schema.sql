CREATE TABLE [requests] (
  [datetime] DATETIME, 
  [service] VARCHAR(32), 
  [uuid] VARCHAR(64), 
  [activity] BOOL);

CREATE INDEX [service_uuid] ON [requests] ([service], [uuid]);