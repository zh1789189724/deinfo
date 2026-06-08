package com.deinfo.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("global_content")
public class GlobalContent {

    @TableId(type = IdType.AUTO)
    private Long id;

    private String title;

    private String titleCn;

    private String content;

    private String contentCn;

    private String summary;

    private String summaryCn;

    private String originalUrl;

    private Long sourceId;

    private String originalLang;

    private String category;

    private String tag;

    private Integer score;

    private String status;

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createdAt;

    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updatedAt;
}
