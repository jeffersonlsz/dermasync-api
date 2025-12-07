-- create_full_db.sql
-- Script unificado e idempotente para inicialização do banco (execução pelo entrypoint do Postgres).
-- Padronizado para usar gen_random_uuid() (pgcrypto).
-- Uso em DEV: recomendado revisar para produção (owners, roles, permissões).

-- 1) Extensões necessárias
-- gen_random_uuid() vem de pgcrypto
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 2) Observação de segurança:
-- O banco/usuário principal tipicamente é criado pelo container via variáveis de ambiente.
-- Este script apenas prepara extensões, tabelas e índices.

-- 3) Tabela users (schema mínimo útil para dev)
CREATE TABLE IF NOT EXISTS public.users (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(50) NOT NULL DEFAULT 'usuario',
  is_active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- 4) Tabela relatos (esqueleto básico)
CREATE TABLE IF NOT EXISTS public.relatos (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES public.users(id) ON DELETE SET NULL,
  titulo TEXT,
  descricao TEXT,
  image_url TEXT,
  metadata JSONB,
  solucao_encontrada BOOLEAN DEFAULT false,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- 5) Garantir coluna token_version em users (para revogação por versão)
ALTER TABLE public.users
  ADD COLUMN IF NOT EXISTS token_version integer DEFAULT 0 NOT NULL;

-- 6) Tabela de refresh tokens
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

-- 7) Tabela de auditoria de sessões
CREATE TABLE IF NOT EXISTS public.sessions_audit (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES public.users(id) ON DELETE SET NULL,
  action text NOT NULL,
  metadata jsonb,
  created_at timestamptz DEFAULT now()
);

-- 8) Índices úteis (dev)
CREATE INDEX IF NOT EXISTS idx_users_email ON public.users(email);
CREATE INDEX IF NOT EXISTS idx_relatos_user ON public.relatos(user_id);

CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON public.refresh_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_token_hash ON public.refresh_tokens(token_hash);

-- 9) Sugestão de limpeza (template) - executar em job separado
-- DELETE FROM public.refresh_tokens WHERE expires_at < now() AND revoked = true;
