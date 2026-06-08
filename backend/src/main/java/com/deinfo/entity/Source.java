package com.deinfo.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("source")
public class Source {

    @TableId(type = IdType.AUTO)
    private Long id;

    private String name;

    private String type;

    private String urlPattern;

    private String lang;

    private Boolean isActive;

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createdAt;

    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updatedAt;
}
