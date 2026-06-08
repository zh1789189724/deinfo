package com.deinfo.dto;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;

import java.util.List;

public record PageResult<T>(List<T> data, long total) {
    public static <T> PageResult<T> from(Page<T> page) {
        return new PageResult<>(page.getRecords(), page.getTotal());
    }

    public static <T> PageResult<T> of(List<T> data, long total) {
        return new PageResult<>(data, total);
    }
}
