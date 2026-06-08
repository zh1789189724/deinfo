-- 信息差发现平台 - 数据库初始化脚本
-- 生成时间: 2026-06-08

CREATE DATABASE IF NOT EXISTS deinfo DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE deinfo;

-- 数据来源表
CREATE TABLE `source` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键',
    `name` VARCHAR(100) NOT NULL COMMENT '来源名称',
    `type` VARCHAR(20) NOT NULL COMMENT '来源类型: wechat/douyin/xiaohongshu/gov/producthunt/hackernews/github/techcrunch/other',
    `url_pattern` VARCHAR(500) DEFAULT NULL COMMENT 'URL匹配模式',
    `lang` VARCHAR(10) DEFAULT 'zh' COMMENT '源语言: zh/en/ja 等',
    `is_active` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否启用',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    INDEX `idx_type` (`type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='数据来源';

-- 用户表
CREATE TABLE `user` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键',
    `username` VARCHAR(50) NOT NULL COMMENT '用户名',
    `password` VARCHAR(100) NOT NULL COMMENT '加密密码',
    `role` VARCHAR(20) NOT NULL DEFAULT 'USER' COMMENT '角色: USER/ADMIN',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户';

-- 优惠/羊毛表
CREATE TABLE `deal` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键',
    `title` VARCHAR(200) NOT NULL COMMENT '标题',
    `description` TEXT COMMENT '详情',
    `summary` VARCHAR(500) DEFAULT NULL COMMENT 'AI生成的摘要',
    `original_url` VARCHAR(500) DEFAULT NULL COMMENT '原始链接',
    `source_id` BIGINT DEFAULT NULL COMMENT '来源ID',
    `category` VARCHAR(30) NOT NULL COMMENT '分类: coupon/discount/flash_sale/gov_subsidy',
    `tag` VARCHAR(200) DEFAULT NULL COMMENT 'AI打标签，逗号分隔',
    `location` VARCHAR(100) DEFAULT NULL COMMENT '区域',
    `validity_end` DATETIME DEFAULT NULL COMMENT '有效截止日期',
    `price` DECIMAL(10,2) DEFAULT 0.00 COMMENT '价格',
    `score` INT DEFAULT 0 COMMENT 'AI价值评分0-100',
    `status` VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT '状态: pending/active/expired',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '采集时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    INDEX `idx_category` (`category`),
    INDEX `idx_status` (`status`),
    INDEX `idx_score` (`score` DESC),
    INDEX `idx_source` (`source_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='优惠/羊毛';

-- 海外精选表（跨语言信息差核心）
CREATE TABLE `global_content` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键',
    `title` VARCHAR(300) NOT NULL COMMENT '原文标题',
    `title_cn` VARCHAR(300) DEFAULT NULL COMMENT 'AI翻译后的中文标题',
    `content` TEXT COMMENT '原文全文',
    `content_cn` TEXT COMMENT 'AI翻译后的中文内容',
    `summary` VARCHAR(500) DEFAULT NULL COMMENT 'AI摘要(原文)',
    `summary_cn` VARCHAR(500) DEFAULT NULL COMMENT 'AI中文摘要',
    `original_url` VARCHAR(500) DEFAULT NULL COMMENT '原文链接',
    `source_id` BIGINT DEFAULT NULL COMMENT '来源ID',
    `original_lang` VARCHAR(10) DEFAULT 'en' COMMENT '源语言',
    `category` VARCHAR(30) NOT NULL COMMENT '分类: tool/startup/industry/policy/trend',
    `tag` VARCHAR(200) DEFAULT NULL COMMENT 'AI打标签',
    `score` INT DEFAULT 0 COMMENT '价值评分0-100',
    `status` VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT '状态: pending/active',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '采集时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    INDEX `idx_category` (`category`),
    INDEX `idx_status` (`status`),
    INDEX `idx_score` (`score` DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='海外精选';

-- 用户爆料表
CREATE TABLE `submit_record` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键',
    `user_id` BIGINT NOT NULL COMMENT '用户ID',
    `title` VARCHAR(200) NOT NULL COMMENT '标题',
    `description` TEXT COMMENT '详情',
    `category` VARCHAR(30) NOT NULL COMMENT '分类: deal/opportunity/tool/info',
    `status` VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT '状态: pending/approved/rejected',
    `reject_reason` VARCHAR(500) DEFAULT NULL COMMENT '拒绝原因',
    `source_info` VARCHAR(500) DEFAULT NULL COMMENT '来源说明',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '提交时间',
    `reviewed_at` DATETIME DEFAULT NULL COMMENT '审核时间',
    PRIMARY KEY (`id`),
    INDEX `idx_user` (`user_id`),
    INDEX `idx_status` (`status`),
    INDEX `idx_category` (`category`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户爆料';

-- 投资机会表
CREATE TABLE `opportunity` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键',
    `title` VARCHAR(200) NOT NULL COMMENT '标题',
    `description` TEXT COMMENT '详情',
    `summary` VARCHAR(500) DEFAULT NULL COMMENT 'AI摘要',
    `category` VARCHAR(30) NOT NULL COMMENT '分类: investment/rental/parttime/policy',
    `source_info` VARCHAR(500) DEFAULT NULL COMMENT '来源说明',
    `status` VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT '状态: pending/approved/rejected',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '提交时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    INDEX `idx_category` (`category`),
    INDEX `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='投资机会';

-- 好用网站/工具表
CREATE TABLE `tool_item` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键',
    `name` VARCHAR(100) NOT NULL COMMENT '名称',
    `url` VARCHAR(500) NOT NULL COMMENT '网址',
    `description` TEXT COMMENT '描述',
    `summary` VARCHAR(500) DEFAULT NULL COMMENT 'AI摘要',
    `tag` VARCHAR(200) DEFAULT NULL COMMENT 'AI标签',
    `source` VARCHAR(200) DEFAULT NULL COMMENT '引用来源',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`id`),
    INDEX `idx_tag` (`tag`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='好用网站/工具';

-- 用户发帖表
CREATE TABLE `post` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键',
    `user_id` BIGINT NOT NULL COMMENT '用户ID',
    `content` TEXT COMMENT '文字内容',
    `images` JSON DEFAULT NULL COMMENT '图片URL数组',
    `link` VARCHAR(500) DEFAULT NULL COMMENT '外链',
    `category` VARCHAR(30) DEFAULT '其他' COMMENT '分类',
    `score` INT DEFAULT 0 COMMENT 'AI质量评分0-100',
    `status` VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT '状态: pending/approved/rejected',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    INDEX `idx_user` (`user_id`),
    INDEX `idx_status` (`status`),
    INDEX `idx_created` (`created_at` DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户发帖';
