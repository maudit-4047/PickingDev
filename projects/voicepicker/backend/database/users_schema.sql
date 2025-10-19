-- Administrative User Management Schema
-- Creates users table for system administrators and warehouse managers
-- Note: This is separate from the 'workers' table which handles warehouse floor staff

-- Drop existing users table if it exists
DROP TABLE IF EXISTS public.users CASCADE;

-- Create administrative users table (separate from warehouse workers)
CREATE TABLE public.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role VARCHAR(20) NOT NULL DEFAULT 'warehouse_manager' CHECK (role IN ('admin', 'warehouse_manager', 'supervisor')),
    
    -- Standard user fields
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    last_login TIMESTAMPTZ,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMPTZ,
    
    -- 2FA fields
    totp_secret VARCHAR(32), -- TOTP secret for 2FA
    is_2fa_enabled BOOLEAN DEFAULT false,
    backup_codes TEXT, -- Comma-separated backup codes
    
    -- Audit fields
    password_changed_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_users_username ON public.users(username);
CREATE INDEX idx_users_email ON public.users(email);
CREATE INDEX idx_users_role ON public.users(role);
CREATE INDEX idx_users_active ON public.users(is_active);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON public.users 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Create user permissions table
CREATE TABLE public.user_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    permission VARCHAR(50) NOT NULL,
    resource VARCHAR(50), -- e.g., 'warehouse_config', 'inventory', etc.
    resource_id UUID, -- specific resource ID (optional)
    granted_at TIMESTAMPTZ DEFAULT NOW(),
    granted_by UUID REFERENCES public.users(id)
);

-- Create indexes for permissions
CREATE INDEX idx_user_permissions_user_id ON public.user_permissions(user_id);
CREATE INDEX idx_user_permissions_permission ON public.user_permissions(permission);
CREATE INDEX idx_user_permissions_resource ON public.user_permissions(resource);

-- Insert default admin user
INSERT INTO public.users (
    id,
    username,
    email,
    password_hash,
    first_name,
    last_name,
    role,
    is_active,
    is_verified
) VALUES (
    gen_random_uuid(),
    'admin',
    'admin@warehouse.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewFTweHSQoHEsYp6', -- password: 'admin123'
    'System',
    'Administrator',
    'admin',
    true,
    true
);

-- Insert warehouse manager user
INSERT INTO public.users (
    id,
    username,
    email,
    password_hash,
    first_name,
    last_name,
    role,
    is_active,
    is_verified
) VALUES (
    gen_random_uuid(),
    'warehouse_mgr',
    'manager@warehouse.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewFTweHSQoHEsYp6', -- password: 'admin123'
    'Warehouse',
    'Manager',
    'warehouse_manager',
    true,
    true
);

-- Insert sample supervisor user
INSERT INTO public.users (
    id,
    username,
    email,
    password_hash,
    first_name,
    last_name,
    role,
    is_active,
    is_verified
) VALUES (
    gen_random_uuid(),
    'supervisor001',
    'supervisor@warehouse.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewFTweHSQoHEsYp6', -- password: 'admin123'
    'Sarah',
    'Supervisor',
    'supervisor',
    true,
    true
);

-- Grant warehouse management permissions to admin and warehouse_manager
INSERT INTO public.user_permissions (user_id, permission, resource)
SELECT u.id, 'manage', 'warehouse_config'
FROM public.users u 
WHERE u.role IN ('admin', 'warehouse_manager');

INSERT INTO public.user_permissions (user_id, permission, resource)
SELECT u.id, 'manage', 'warehouse_templates'
FROM public.users u 
WHERE u.role IN ('admin', 'warehouse_manager');

INSERT INTO public.user_permissions (user_id, permission, resource)
SELECT u.id, 'manage', 'location_zones'
FROM public.users u 
WHERE u.role IN ('admin', 'warehouse_manager');

-- Enable Row Level Security
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_permissions ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for users table
CREATE POLICY "Users can view their own profile" ON public.users
    FOR SELECT USING (auth.uid()::text = id::text);

CREATE POLICY "Admins can view all users" ON public.users
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.users 
            WHERE id::text = auth.uid()::text 
            AND role IN ('admin', 'warehouse_manager')
        )
    );

CREATE POLICY "Admins can manage users" ON public.users
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM public.users 
            WHERE id::text = auth.uid()::text 
            AND role = 'admin'
        )
    );

-- Create RLS policies for permissions table
CREATE POLICY "Users can view their own permissions" ON public.user_permissions
    FOR SELECT USING (user_id::text = auth.uid()::text);

CREATE POLICY "Admins can manage all permissions" ON public.user_permissions
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM public.users 
            WHERE id::text = auth.uid()::text 
            AND role = 'admin'
        )
    );

-- Create function to check user permissions
CREATE OR REPLACE FUNCTION public.has_permission(
    user_id_param UUID,
    permission_param VARCHAR,
    resource_param VARCHAR DEFAULT NULL,
    resource_id_param UUID DEFAULT NULL
)
RETURNS BOOLEAN
SECURITY DEFINER
SET search_path = public
LANGUAGE plpgsql
AS $$
BEGIN
    -- Check if user is admin (has all permissions)
    IF EXISTS (
        SELECT 1 FROM public.users 
        WHERE id = user_id_param 
        AND role = 'admin' 
        AND is_active = true
    ) THEN
        RETURN true;
    END IF;
    
    -- Check specific permission
    RETURN EXISTS (
        SELECT 1 FROM public.user_permissions up
        JOIN public.users u ON u.id = up.user_id
        WHERE up.user_id = user_id_param
        AND u.is_active = true
        AND up.permission = permission_param
        AND (resource_param IS NULL OR up.resource = resource_param)
        AND (resource_id_param IS NULL OR up.resource_id = resource_id_param)
    );
END;
$$;

-- Comments for documentation
COMMENT ON TABLE public.users IS 'User accounts with authentication and role-based access';
COMMENT ON TABLE public.user_permissions IS 'Granular permissions for users on specific resources';
COMMENT ON FUNCTION public.has_permission IS 'Check if a user has a specific permission on a resource';

-- Show created users
SELECT 
    username, 
    email, 
    role, 
    is_active,
    created_at
FROM public.users
ORDER BY role, username;