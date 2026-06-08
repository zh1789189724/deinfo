package com.deinfo.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("tool_item")
public class ToolItem {

    @TableId(type = IdType.AUTO)
    private Long id;

    private String name;

    private String url;

    private String description;

    private String summary;

    private String tag;

    private String source;

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createdAt;
}
