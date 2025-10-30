-- SQL queries to check for and clean up duplicate users

-- 1. Check for duplicate users by username
SELECT username, COUNT(*) as count 
FROM users 
GROUP BY username 
HAVING COUNT(*) > 1;

-- 2. Check for duplicate users by email  
SELECT email, COUNT(*) as count 
FROM users 
GROUP BY email 
HAVING COUNT(*) > 1;

-- 3. Show duplicate users with their details
SELECT u1.id, u1.username, u1.email, u1.created_at
FROM users u1
JOIN (
    SELECT username, email
    FROM users
    GROUP BY username, email
    HAVING COUNT(*) > 1
) u2 ON u1.username = u2.username AND u1.email = u2.email
ORDER BY u1.username, u1.created_at;

-- 4. Clean up duplicates (CAREFUL: Run this only after backing up your data)
-- This keeps the oldest user for each username/email combination
/*
DELETE u1 FROM users u1
INNER JOIN users u2 
WHERE u1.id > u2.id 
AND (u1.username = u2.username OR u1.email = u2.email);
*/

-- 5. Alternative cleanup: Keep the newest user instead
/*
DELETE u1 FROM users u1
INNER JOIN users u2 
WHERE u1.id < u2.id 
AND (u1.username = u2.username OR u1.email = u2.email);
*/

-- 6. Check profiles without corresponding users (orphaned profiles)
SELECT p.id, p.name, p.user_id
FROM profiles p
LEFT JOIN users u ON p.user_id = u.id
WHERE u.id IS NULL;

-- 7. Check users without profiles
SELECT u.id, u.username, u.email
FROM users u
LEFT JOIN profiles p ON u.id = p.user_id
WHERE p.id IS NULL;