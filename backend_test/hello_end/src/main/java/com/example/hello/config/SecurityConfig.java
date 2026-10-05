package com.example.hello.config;

import jakarta.servlet.http.HttpServletResponse;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.config.annotation.authentication.configuration.AuthenticationConfiguration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.core.userdetails.User;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.provisioning.InMemoryUserDetailsManager;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.context.HttpSessionSecurityContextRepository;
import org.springframework.security.web.context.SecurityContextRepository;

/**
 * Spring Security 安全配置类
 * - 放行 POST /login，其余接口（含 /hello）必须认证
 * - 未认证请求统一返回 401
 * - 用户信息保存在内存中，密码使用 BCrypt 加密
 */
@Configuration
@EnableWebSecurity
public class SecurityConfig {

    /**
     * 安全过滤器链：定义授权规则与异常处理
     */
    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
                // 纯前后端分离接口，关闭 CSRF（否则 POST /login 会被拦截要求 CSRF Token）
                .csrf(csrf -> csrf.disable())
                // 登录成功后通过 Session 维持认证状态
                .sessionManagement(session ->
                        session.sessionCreationPolicy(SessionCreationPolicy.IF_REQUIRED))
                // 授权规则
                .authorizeHttpRequests(auth -> auth
                        // 登录接口放行
                        .requestMatchers(HttpMethod.POST, "/login").permitAll()
                        // HelloWorld 接口必须认证
                        .requestMatchers(HttpMethod.GET, "/hello").authenticated()
                        // 其他请求同样需要认证
                        .anyRequest().authenticated())
                // 未认证访问受保护资源时返回 401（默认会返回 403/跳转登录页）
                .exceptionHandling(ex -> ex.authenticationEntryPoint((request, response, authException) ->
                        response.sendError(HttpServletResponse.SC_UNAUTHORIZED, "未认证，请先登录")))
                // 关闭默认表单登录与 HTTP Basic，使用自定义 /login 接口
                .formLogin(form -> form.disable())
                .httpBasic(basic -> basic.disable());

        return http.build();
    }

    /**
     * 密码编码器：BCrypt 单向哈希
     */
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    /**
     * 内存用户详情服务：固定测试账号 test / 123456（密码以 BCrypt 密文存储）
     */
    @Bean
    public UserDetailsService userDetailsService(PasswordEncoder passwordEncoder) {
        UserDetails testUser = User.builder()
                .username("test")
                .password(passwordEncoder.encode("123456"))
                .roles("USER")
                .build();
        return new InMemoryUserDetailsManager(testUser);
    }

    /**
     * 认证管理器：在 /login 接口中手动调用执行账号密码校验
     */
    @Bean
    public AuthenticationManager authenticationManager(AuthenticationConfiguration configuration) throws Exception {
        return configuration.getAuthenticationManager();
    }

    /**
     * 认证信息仓库：登录成功后将 SecurityContext 持久化到 HttpSession
     */
    @Bean
    public SecurityContextRepository securityContextRepository() {
        return new HttpSessionSecurityContextRepository();
    }
}
