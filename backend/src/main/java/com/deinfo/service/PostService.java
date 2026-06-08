package com.deinfo.service;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.deinfo.entity.Post;
import com.deinfo.mapper.PostMapper;
import org.springframework.stereotype.Service;

@Service
public class PostService extends ServiceImpl<PostMapper, Post> {
}
