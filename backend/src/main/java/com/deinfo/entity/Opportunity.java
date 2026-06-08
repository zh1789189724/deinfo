package com.deinfo.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("opportunity")
public class Opportunity {

    @TableId(type = IdType.AUTO)
    private Long id;

    private String title;

    private String description;

    private String summary;

    private String category;

    private String sourceInfo;

    private String status;

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createdAt;

    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updatedAt;
}
