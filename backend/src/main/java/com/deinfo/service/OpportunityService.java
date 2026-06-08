package com.deinfo.service;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.deinfo.entity.Opportunity;
import com.deinfo.mapper.OpportunityMapper;
import org.springframework.stereotype.Service;

@Service
public class OpportunityService extends ServiceImpl<OpportunityMapper, Opportunity> {
}
