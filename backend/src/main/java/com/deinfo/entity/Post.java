package com.deinfo.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("post")
public class Post {

    @TableId(type = IdType.AUTO)
    private Long id;

    private Long userId;

    private String content;

    private String images;

    private String link;

    private String category;

    private Integer score;

    private String status;

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createdAt;

    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updatedAt;
}
