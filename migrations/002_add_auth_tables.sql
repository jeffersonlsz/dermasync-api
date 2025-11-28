-- migrations/002_add_auth_tables.sql
-- Adiciona coluna token_version e tabelas refresh_tokens e sessions_audit


CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";


-- coluna token_version para revogação por versão
ALTER TABLE public.users
ADD COLUMN IF NOT EXISTS token_version integer DEFAULT 0 NOT NULL;


-- tabela de refresh tokens
CREATE TABLE IF NOT EXISTS public.refresh_tokens (
id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
user_id uuid REFERENCES public.users(id) ON DELETE CASCADE,
token_hash text NOT NULL,
revoked boolean DEFAULT false,
created_at timestamptz DEFAULT now(),
last_used_at timestamptz,
expires_at timestamptz,
ip text,
user_agent text
);


CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON public.refresh_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_token_hash ON public.refresh_tokens(token_hash);


-- tabela de auditoria de sessões
CREATE TABLE IF NOT EXISTS public.sessions_audit (
id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
user_id uuid,
action text NOT NULL,
metadata jsonb,
created_at timestamptz DEFAULT now()
);


-- opcional: clean old tokens (template)
-- DELETE FROM public.refresh_tokens WHERE expires_at < now() AND revoked = true;