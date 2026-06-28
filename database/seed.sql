USE votehub_db;

INSERT INTO users 
(full_name, email, phone, password_hash, role, status, email_verified)
VALUES
('System Admin', 'admin@votehub.com', '9999999999', '\\\', 'admin', 'active', 1),
('Demo Voter', 'voter@votehub.com', '8888888888', '\\\', 'voter', 'active', 1);

INSERT INTO voters
(user_id, voter_uid, date_of_birth, gender, address, id_type, id_number, verification_status)
VALUES
(2, 'VH-VOTER-1001', '2002-05-15', 'Male', 'Demo Address', 'College ID', 'COLL1001', 'approved');

INSERT INTO candidates
(full_name, party_name, symbol, description)
VALUES
('Rahul Sharma', 'Student Unity Party', 'symbol_1.png', 'Focused on student welfare and campus development.'),
('Aisha Khan', 'Youth Progress Party', 'symbol_2.png', 'Focused on academic support and student activities.'),
('Neha Verma', 'Future Leaders Party', 'symbol_3.png', 'Focused on innovation and digital campus initiatives.');

INSERT INTO elections
(title, description, start_datetime, end_datetime, status, result_published, created_by)
VALUES
('Student Council Election 2026', 'Election for selecting student council representatives.', '2026-07-01 09:00:00', '2026-07-01 17:00:00', 'draft', 0, 1);

INSERT INTO election_candidates
(election_id, candidate_id)
VALUES
(1,1),
(1,2),
(1,3);

INSERT INTO settings
(setting_key, setting_value)
VALUES
('app_name', 'VoteHub'),
('college_project_title', 'A Secure Online Voting & Election Management System'),
('result_visibility', 'admin_only');
