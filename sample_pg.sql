create table kc
(
    bh integer not null
        constraint kc_pk
            primary key,
    mz varchar(100),
    sl integer not null
);

comment on table public.kc is '库存';
comment on column public.kc.bh is '编号';
comment on constraint kc_pk on public.kc is '主键';
comment on column public.kc.mz is '名字';
comment on column public.kc.sl is '数量';
