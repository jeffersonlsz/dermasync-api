-- 01-create-db.sql
-- Executado automaticamente pelo entrypoint do Postgres na primeira subida do container.

-- 1) Extensões úteis (Postgres)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 2) Segurança mínima / verificações
-- (o banco já é criado pelo postgres via variáveis de ambiente, mas garantimos privilégios)
-- NOTE: O usuário e db são criados pelo container, então esse script foca em preparar extensões.

-- 3) Tabela users (schema mínimo útil para dev)
CREATE TABLE IF NOT EXISTS public.users (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(50) NOT NULL DEFAULT 'usuario',
  is_active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- 4) Tabela relatos (esqueleto básico)
CREATE TABLE IF NOT EXISTS public.relatos (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id uuid REFERENCES public.users(id) ON DELETE SET NULL,
  titulo TEXT,
  descricao TEXT,
  image_url TEXT,
  metadata JSONB,
  solucao_encontrada BOOLEAN DEFAULT false,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- 5) Índices úteis (dev)
CREATE INDEX IF NOT EXISTS idx_users_email ON public.users(email);
CREATE INDEX IF NOT EXISTS idx_relatos_user ON public.relatos(user_id);
