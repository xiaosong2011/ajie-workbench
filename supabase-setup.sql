-- ============================================
-- 阿杰工作台 · Supabase 建表脚本
-- ============================================
-- 使用方法：
-- 1. 登录 https://supabase.com 创建新项目
-- 2. 左侧菜单点「SQL Editor」
-- 3. 将本文件全部内容粘贴进去，点「Run」执行
-- 4. 执行完成后，去「Settings → API」获取 URL 和 anon key
-- ============================================

-- 创建工作台数据表（如果不存在）
CREATE TABLE IF NOT EXISTS workbench_data (
  workspace_id TEXT PRIMARY KEY,
  data JSONB NOT NULL DEFAULT '{}'::jsonb,
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- 禁用行级安全（个人工具，允许匿名读写）
ALTER TABLE workbench_data DISABLE ROW LEVEL SECURITY;

-- 授权匿名用户所有操作权限
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE workbench_data TO anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE workbench_data TO authenticated;

-- 启用实时订阅（Postgres Changes）
-- 需要在 Supabase 后台手动操作：
-- Settings → Database → Replication → 添加 workbench_data 表到 publication
DO $$
BEGIN
  -- 尝试将表加入 supabase_realtime publication
  -- 如果已存在会报错，忽略即可
  ALTER PUBLICATION supabase_realtime ADD TABLE workbench_data;
EXCEPTION WHEN OTHERS THEN
  RAISE NOTICE '表可能已在 publication 中，或需要手动在后台添加';
END $$;

-- 更新时间触发器（可选：自动更新 updated_at）
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS workbench_data_updated_at ON workbench_data;
CREATE TRIGGER workbench_data_updated_at
  BEFORE UPDATE ON workbench_data
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at();

-- 完成提示
SELECT '✅ 建表完成！现在去 Settings → API 获取 Project URL 和 anon key' as message;
