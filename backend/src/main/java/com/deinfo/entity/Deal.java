package com.deinfo.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
@TableName("deal")
public class Deal {

    @TableId(type = IdType.AUTO)
    private Long id;

    private String title;

    private String description;

    private String summary;

    private String originalUrl;

    private Long sourceId;

    private String category;

    private String tag;

    private String location;

    private LocalDateTime validityEnd;

    private BigDecimal price;

    private Integer score;

    private String status;

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createdAt;

    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updatedAt;
}
