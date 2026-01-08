-- ============================================
-- 数据库索引优化建议
-- ============================================
-- 这些索引将提高 KPI 和 Rating Distribution 查询的性能

-- 1. 复合索引：支持按航空公司和日期范围查询（KPI 查询）
CREATE INDEX IF NOT EXISTS idx_reviews_airline_date 
ON reviews("airlineName", "dateReview");

-- 2. 复合索引：支持按航空公司和评分查询（Rating Distribution）
CREATE INDEX IF NOT EXISTS idx_reviews_airline_score 
ON reviews("airlineName", score) 
WHERE score IS NOT NULL;

-- 3. 路由索引：支持目的地筛选（使用 GIN 索引支持 LIKE 查询）
CREATE INDEX IF NOT EXISTS idx_reviews_route_gin 
ON reviews USING gin(route gin_trgm_ops)
WHERE route IS NOT NULL;

-- 注意：GIN 索引需要 pg_trgm 扩展
-- 如果未安装，运行: CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 4. 部分索引：仅对有效评分的评论建立索引（节省空间）
CREATE INDEX IF NOT EXISTS idx_reviews_airline_date_score 
ON reviews("airlineName", "dateReview", score)
WHERE score IS NOT NULL AND "dateReview" IS NOT NULL;

-- 5. 覆盖索引：包含常用查询字段（减少回表）
CREATE INDEX IF NOT EXISTS idx_reviews_covering 
ON reviews("airlineName", "dateReview", score, route)
WHERE score IS NOT NULL;

-- 验证索引
-- SELECT indexname, indexdef 
-- FROM pg_indexes 
-- WHERE tablename = 'reviews';

