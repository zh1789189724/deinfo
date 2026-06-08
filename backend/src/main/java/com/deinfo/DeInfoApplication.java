package com.deinfo;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
@MapperScan("com.deinfo.mapper")
public class DeInfoApplication {
    public static void main(String[] args) {
        SpringApplication.run(DeInfoApplication.class, args);
    }
}
