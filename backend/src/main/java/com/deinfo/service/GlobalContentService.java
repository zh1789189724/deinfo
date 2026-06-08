package com.deinfo.service;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.deinfo.entity.GlobalContent;
import com.deinfo.mapper.GlobalContentMapper;
import org.springframework.stereotype.Service;

@Service
public class GlobalContentService extends ServiceImpl<GlobalContentMapper, GlobalContent> {
}
