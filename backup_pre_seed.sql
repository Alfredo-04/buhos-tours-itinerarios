--
-- PostgreSQL database dump
--

\restrict jthRzTrbLxTvtZN6tEGEAUGf4fa61DO82tkYJidOLydeMFm1A3CxD4BJCt43dRt

-- Dumped from database version 18.6
-- Dumped by pg_dump version 18.6

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: public; Type: SCHEMA; Schema: -; Owner: postgres
--

-- *not* creating schema, since initdb creates it


ALTER SCHEMA public OWNER TO postgres;

--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: postgres
--

COMMENT ON SCHEMA public IS '';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO postgres;

--
-- Name: atractivo; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.atractivo (
    id_atractivo integer NOT NULL,
    nombre character varying(100) NOT NULL,
    descripcion character varying(500),
    latitud numeric(10,7),
    longitud numeric(10,7),
    direccion character varying(200),
    horario_apertura time without time zone,
    horario_cierre time without time zone,
    costo_entrada numeric(10,2) NOT NULL,
    tiempo_visita_estimado integer,
    dias_cerrado text,
    imagen_url character varying(255),
    fecha_inicio date,
    fecha_fin date,
    afecta_rutas boolean NOT NULL,
    sensible_al_clima boolean NOT NULL,
    tipo_clima_ideal character varying(100),
    id_subcategoria integer NOT NULL,
    id_proveedor integer NOT NULL,
    deleted_at timestamp without time zone
);


ALTER TABLE public.atractivo OWNER TO postgres;

--
-- Name: atractivo_id_atractivo_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.atractivo_id_atractivo_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.atractivo_id_atractivo_seq OWNER TO postgres;

--
-- Name: atractivo_id_atractivo_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.atractivo_id_atractivo_seq OWNED BY public.atractivo.id_atractivo;


--
-- Name: categoria; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.categoria (
    id_categoria integer NOT NULL,
    nombre character varying(50) NOT NULL,
    descripcion character varying(200),
    deleted_at timestamp without time zone
);


ALTER TABLE public.categoria OWNER TO postgres;

--
-- Name: categoria_id_categoria_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.categoria_id_categoria_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.categoria_id_categoria_seq OWNER TO postgres;

--
-- Name: categoria_id_categoria_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.categoria_id_categoria_seq OWNED BY public.categoria.id_categoria;


--
-- Name: consulta_nsga2; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.consulta_nsga2 (
    id_consulta integer NOT NULL,
    fecha timestamp without time zone NOT NULL,
    id_generacion integer,
    num_atractivos integer NOT NULL,
    num_transportes integer NOT NULL,
    presupuesto numeric(10,2) NOT NULL,
    tiempo_disponible_horas numeric(5,2) NOT NULL,
    intereses text,
    tamano_poblacion integer NOT NULL,
    generaciones integer NOT NULL,
    prob_cruce numeric(4,2) NOT NULL,
    prob_mutacion numeric(4,2) NOT NULL,
    num_soluciones integer NOT NULL,
    mejor_afinidad numeric(5,4),
    mejor_tiempo numeric(10,2),
    soluciones_viables integer NOT NULL,
    todas_exceden boolean NOT NULL,
    tiempo_ejecucion_seg numeric(6,2),
    convergencia numeric(5,4),
    diversidad_final numeric(5,4)
);


ALTER TABLE public.consulta_nsga2 OWNER TO postgres;

--
-- Name: consulta_nsga2_id_consulta_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.consulta_nsga2_id_consulta_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.consulta_nsga2_id_consulta_seq OWNER TO postgres;

--
-- Name: consulta_nsga2_id_consulta_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.consulta_nsga2_id_consulta_seq OWNED BY public.consulta_nsga2.id_consulta;


--
-- Name: generacion; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.generacion (
    id_generacion integer NOT NULL,
    fecha_generacion timestamp without time zone NOT NULL,
    id_usuario integer NOT NULL,
    fecha_inicio_viaje date NOT NULL,
    fecha_fin_viaje date NOT NULL,
    presupuesto numeric(10,2) NOT NULL,
    cantidad_soluciones integer NOT NULL,
    observaciones text
);


ALTER TABLE public.generacion OWNER TO postgres;

--
-- Name: generacion_id_generacion_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.generacion_id_generacion_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.generacion_id_generacion_seq OWNER TO postgres;

--
-- Name: generacion_id_generacion_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.generacion_id_generacion_seq OWNED BY public.generacion.id_generacion;


--
-- Name: itinerario; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.itinerario (
    id_itinerario integer NOT NULL,
    id_generacion integer NOT NULL,
    numero_solucion integer NOT NULL,
    estado character varying(20) NOT NULL,
    tiempo_total_estimado numeric(10,2),
    codigo_confirmacion uuid,
    voucher_generado boolean NOT NULL,
    deleted_at timestamp without time zone
);


ALTER TABLE public.itinerario OWNER TO postgres;

--
-- Name: itinerario_detalle; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.itinerario_detalle (
    id_detalle integer NOT NULL,
    id_itinerario integer NOT NULL,
    id_atractivo integer NOT NULL,
    id_transporte integer,
    dia integer NOT NULL,
    orden integer NOT NULL,
    hora_llegada_estimada time without time zone,
    hora_salida_estimada time without time zone,
    tiempo_traslado_desde_anterior integer
);


ALTER TABLE public.itinerario_detalle OWNER TO postgres;

--
-- Name: itinerario_detalle_id_detalle_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.itinerario_detalle_id_detalle_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.itinerario_detalle_id_detalle_seq OWNER TO postgres;

--
-- Name: itinerario_detalle_id_detalle_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.itinerario_detalle_id_detalle_seq OWNED BY public.itinerario_detalle.id_detalle;


--
-- Name: itinerario_detalle_trafico; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.itinerario_detalle_trafico (
    id_detalle integer NOT NULL,
    id_patron integer NOT NULL
);


ALTER TABLE public.itinerario_detalle_trafico OWNER TO postgres;

--
-- Name: itinerario_id_itinerario_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.itinerario_id_itinerario_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.itinerario_id_itinerario_seq OWNER TO postgres;

--
-- Name: itinerario_id_itinerario_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.itinerario_id_itinerario_seq OWNED BY public.itinerario.id_itinerario;


--
-- Name: patron_trafico; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.patron_trafico (
    id_patron integer NOT NULL,
    id_zona integer NOT NULL,
    dia_semana character varying(20) NOT NULL,
    hora_inicio time without time zone NOT NULL,
    hora_fin time without time zone NOT NULL,
    factor_congestion numeric(4,2) NOT NULL,
    color_nivel character varying(20) NOT NULL,
    tipo character varying(20) NOT NULL,
    deleted_at timestamp without time zone
);


ALTER TABLE public.patron_trafico OWNER TO postgres;

--
-- Name: patron_trafico_id_patron_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.patron_trafico_id_patron_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.patron_trafico_id_patron_seq OWNER TO postgres;

--
-- Name: patron_trafico_id_patron_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.patron_trafico_id_patron_seq OWNED BY public.patron_trafico.id_patron;


--
-- Name: proveedor; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.proveedor (
    id_proveedor integer NOT NULL,
    razon_social character varying(100) NOT NULL,
    tipo character varying(50),
    contacto_nombre character varying(100),
    contacto_telefono character varying(20),
    contacto_email character varying(100),
    tarifa_especial numeric(10,2),
    observaciones text,
    deleted_at timestamp without time zone
);


ALTER TABLE public.proveedor OWNER TO postgres;

--
-- Name: proveedor_id_proveedor_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.proveedor_id_proveedor_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.proveedor_id_proveedor_seq OWNER TO postgres;

--
-- Name: proveedor_id_proveedor_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.proveedor_id_proveedor_seq OWNED BY public.proveedor.id_proveedor;


--
-- Name: rol; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.rol (
    id_rol integer NOT NULL,
    nombre character varying(20) NOT NULL
);


ALTER TABLE public.rol OWNER TO postgres;

--
-- Name: rol_id_rol_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.rol_id_rol_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.rol_id_rol_seq OWNER TO postgres;

--
-- Name: rol_id_rol_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.rol_id_rol_seq OWNED BY public.rol.id_rol;


--
-- Name: subcategoria; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.subcategoria (
    id_subcategoria integer NOT NULL,
    nombre character varying(50) NOT NULL,
    descripcion character varying(200),
    id_categoria integer NOT NULL,
    deleted_at timestamp without time zone
);


ALTER TABLE public.subcategoria OWNER TO postgres;

--
-- Name: subcategoria_id_subcategoria_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.subcategoria_id_subcategoria_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.subcategoria_id_subcategoria_seq OWNER TO postgres;

--
-- Name: subcategoria_id_subcategoria_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.subcategoria_id_subcategoria_seq OWNED BY public.subcategoria.id_subcategoria;


--
-- Name: tipo_cambio; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tipo_cambio (
    id_tipo_cambio integer NOT NULL,
    fecha timestamp without time zone NOT NULL,
    valor_compra numeric(10,4) NOT NULL,
    valor_venta numeric(10,4) NOT NULL,
    fuente character varying(20) NOT NULL,
    id_usuario integer
);


ALTER TABLE public.tipo_cambio OWNER TO postgres;

--
-- Name: tipo_cambio_id_tipo_cambio_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.tipo_cambio_id_tipo_cambio_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tipo_cambio_id_tipo_cambio_seq OWNER TO postgres;

--
-- Name: tipo_cambio_id_tipo_cambio_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.tipo_cambio_id_tipo_cambio_seq OWNED BY public.tipo_cambio.id_tipo_cambio;


--
-- Name: transporte; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.transporte (
    id_transporte integer NOT NULL,
    nombre character varying(100) NOT NULL,
    tipo character varying(20) NOT NULL,
    capacidad integer,
    horario_inicio time without time zone,
    horario_fin time without time zone,
    costo numeric(10,2) NOT NULL,
    tipo_costo character varying(20) NOT NULL,
    velocidad_promedio_kmh numeric(5,2) NOT NULL,
    deleted_at timestamp without time zone
);


ALTER TABLE public.transporte OWNER TO postgres;

--
-- Name: transporte_id_transporte_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.transporte_id_transporte_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.transporte_id_transporte_seq OWNER TO postgres;

--
-- Name: transporte_id_transporte_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.transporte_id_transporte_seq OWNED BY public.transporte.id_transporte;


--
-- Name: turista; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.turista (
    id_turista integer NOT NULL,
    id_usuario integer,
    nombres character varying(80) NOT NULL,
    apellidos character varying(80) NOT NULL,
    nacionalidad character varying(50),
    procedencia character varying(50),
    nro_documento character varying(20),
    fecha_nacimiento date,
    pasaporte_vencimiento date,
    email character varying(100),
    telefono character varying(20)
);


ALTER TABLE public.turista OWNER TO postgres;

--
-- Name: turista_id_turista_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.turista_id_turista_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.turista_id_turista_seq OWNER TO postgres;

--
-- Name: turista_id_turista_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.turista_id_turista_seq OWNED BY public.turista.id_turista;


--
-- Name: usuario; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.usuario (
    id_usuario integer NOT NULL,
    nombres character varying(80) NOT NULL,
    apellidos character varying(80) NOT NULL,
    email character varying(100) NOT NULL,
    contrasenia character varying(255) NOT NULL,
    id_rol integer NOT NULL,
    fecha_registro date NOT NULL,
    deleted_at timestamp without time zone,
    two_factor_secret character varying(32),
    two_factor_enabled boolean NOT NULL,
    two_factor_confirmed_at timestamp without time zone,
    must_change_password boolean NOT NULL,
    temp_password_expires_at timestamp without time zone,
    reset_token character varying(255),
    reset_token_expires_at timestamp without time zone,
    reset_token_used boolean NOT NULL
);


ALTER TABLE public.usuario OWNER TO postgres;

--
-- Name: usuario_id_usuario_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.usuario_id_usuario_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.usuario_id_usuario_seq OWNER TO postgres;

--
-- Name: usuario_id_usuario_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.usuario_id_usuario_seq OWNED BY public.usuario.id_usuario;


--
-- Name: viaje_turista; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.viaje_turista (
    id_itinerario integer NOT NULL,
    id_turista integer NOT NULL
);


ALTER TABLE public.viaje_turista OWNER TO postgres;

--
-- Name: zona_trafico; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.zona_trafico (
    id_zona integer NOT NULL,
    nombre character varying(100) NOT NULL,
    tipo_geometria character varying(20) NOT NULL,
    geometria_wkt text NOT NULL,
    tipo character varying(20) NOT NULL,
    deleted_at timestamp without time zone
);


ALTER TABLE public.zona_trafico OWNER TO postgres;

--
-- Name: zona_trafico_id_zona_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.zona_trafico_id_zona_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.zona_trafico_id_zona_seq OWNER TO postgres;

--
-- Name: zona_trafico_id_zona_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.zona_trafico_id_zona_seq OWNED BY public.zona_trafico.id_zona;


--
-- Name: atractivo id_atractivo; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.atractivo ALTER COLUMN id_atractivo SET DEFAULT nextval('public.atractivo_id_atractivo_seq'::regclass);


--
-- Name: categoria id_categoria; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.categoria ALTER COLUMN id_categoria SET DEFAULT nextval('public.categoria_id_categoria_seq'::regclass);


--
-- Name: consulta_nsga2 id_consulta; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.consulta_nsga2 ALTER COLUMN id_consulta SET DEFAULT nextval('public.consulta_nsga2_id_consulta_seq'::regclass);


--
-- Name: generacion id_generacion; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.generacion ALTER COLUMN id_generacion SET DEFAULT nextval('public.generacion_id_generacion_seq'::regclass);


--
-- Name: itinerario id_itinerario; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.itinerario ALTER COLUMN id_itinerario SET DEFAULT nextval('public.itinerario_id_itinerario_seq'::regclass);


--
-- Name: itinerario_detalle id_detalle; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.itinerario_detalle ALTER COLUMN id_detalle SET DEFAULT nextval('public.itinerario_detalle_id_detalle_seq'::regclass);


--
-- Name: patron_trafico id_patron; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.patron_trafico ALTER COLUMN id_patron SET DEFAULT nextval('public.patron_trafico_id_patron_seq'::regclass);


--
-- Name: proveedor id_proveedor; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.proveedor ALTER COLUMN id_proveedor SET DEFAULT nextval('public.proveedor_id_proveedor_seq'::regclass);


--
-- Name: rol id_rol; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rol ALTER COLUMN id_rol SET DEFAULT nextval('public.rol_id_rol_seq'::regclass);


--
-- Name: subcategoria id_subcategoria; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.subcategoria ALTER COLUMN id_subcategoria SET DEFAULT nextval('public.subcategoria_id_subcategoria_seq'::regclass);


--
-- Name: tipo_cambio id_tipo_cambio; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tipo_cambio ALTER COLUMN id_tipo_cambio SET DEFAULT nextval('public.tipo_cambio_id_tipo_cambio_seq'::regclass);


--
-- Name: transporte id_transporte; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transporte ALTER COLUMN id_transporte SET DEFAULT nextval('public.transporte_id_transporte_seq'::regclass);


--
-- Name: turista id_turista; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.turista ALTER COLUMN id_turista SET DEFAULT nextval('public.turista_id_turista_seq'::regclass);


--
-- Name: usuario id_usuario; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuario ALTER COLUMN id_usuario SET DEFAULT nextval('public.usuario_id_usuario_seq'::regclass);


--
-- Name: zona_trafico id_zona; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.zona_trafico ALTER COLUMN id_zona SET DEFAULT nextval('public.zona_trafico_id_zona_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.alembic_version (version_num) FROM stdin;
b2389a0d44e0
\.


--
-- Data for Name: atractivo; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.atractivo (id_atractivo, nombre, descripcion, latitud, longitud, direccion, horario_apertura, horario_cierre, costo_entrada, tiempo_visita_estimado, dias_cerrado, imagen_url, fecha_inicio, fecha_fin, afecta_rutas, sensible_al_clima, tipo_clima_ideal, id_subcategoria, id_proveedor, deleted_at) FROM stdin;
\.


--
-- Data for Name: categoria; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.categoria (id_categoria, nombre, descripcion, deleted_at) FROM stdin;
\.


--
-- Data for Name: consulta_nsga2; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.consulta_nsga2 (id_consulta, fecha, id_generacion, num_atractivos, num_transportes, presupuesto, tiempo_disponible_horas, intereses, tamano_poblacion, generaciones, prob_cruce, prob_mutacion, num_soluciones, mejor_afinidad, mejor_tiempo, soluciones_viables, todas_exceden, tiempo_ejecucion_seg, convergencia, diversidad_final) FROM stdin;
\.


--
-- Data for Name: generacion; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.generacion (id_generacion, fecha_generacion, id_usuario, fecha_inicio_viaje, fecha_fin_viaje, presupuesto, cantidad_soluciones, observaciones) FROM stdin;
\.


--
-- Data for Name: itinerario; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.itinerario (id_itinerario, id_generacion, numero_solucion, estado, tiempo_total_estimado, codigo_confirmacion, voucher_generado, deleted_at) FROM stdin;
\.


--
-- Data for Name: itinerario_detalle; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.itinerario_detalle (id_detalle, id_itinerario, id_atractivo, id_transporte, dia, orden, hora_llegada_estimada, hora_salida_estimada, tiempo_traslado_desde_anterior) FROM stdin;
\.


--
-- Data for Name: itinerario_detalle_trafico; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.itinerario_detalle_trafico (id_detalle, id_patron) FROM stdin;
\.


--
-- Data for Name: patron_trafico; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.patron_trafico (id_patron, id_zona, dia_semana, hora_inicio, hora_fin, factor_congestion, color_nivel, tipo, deleted_at) FROM stdin;
\.


--
-- Data for Name: proveedor; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.proveedor (id_proveedor, razon_social, tipo, contacto_nombre, contacto_telefono, contacto_email, tarifa_especial, observaciones, deleted_at) FROM stdin;
\.


--
-- Data for Name: rol; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.rol (id_rol, nombre) FROM stdin;
1	admin
2	agente
3	turista
\.


--
-- Data for Name: subcategoria; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.subcategoria (id_subcategoria, nombre, descripcion, id_categoria, deleted_at) FROM stdin;
\.


--
-- Data for Name: tipo_cambio; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.tipo_cambio (id_tipo_cambio, fecha, valor_compra, valor_venta, fuente, id_usuario) FROM stdin;
\.


--
-- Data for Name: transporte; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.transporte (id_transporte, nombre, tipo, capacidad, horario_inicio, horario_fin, costo, tipo_costo, velocidad_promedio_kmh, deleted_at) FROM stdin;
\.


--
-- Data for Name: turista; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.turista (id_turista, id_usuario, nombres, apellidos, nacionalidad, procedencia, nro_documento, fecha_nacimiento, pasaporte_vencimiento, email, telefono) FROM stdin;
\.


--
-- Data for Name: usuario; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.usuario (id_usuario, nombres, apellidos, email, contrasenia, id_rol, fecha_registro, deleted_at, two_factor_secret, two_factor_enabled, two_factor_confirmed_at, must_change_password, temp_password_expires_at, reset_token, reset_token_expires_at, reset_token_used) FROM stdin;
1	Administrador	Sistema	admin@buhostours.com	pbkdf2:sha256:600000$QswCbSMA7nuqL0oS$d3c0cc6b39540d70b7fe9097fa92cf5892a44c59096f200f410029f331a4fcce	1	2026-10-07	\N	ZYCQ6MCUQIWIMFBPLIOOJRCOZQZEXCHB	t	2026-10-07 08:22:22.402106	f	\N	\N	\N	f
\.


--
-- Data for Name: viaje_turista; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.viaje_turista (id_itinerario, id_turista) FROM stdin;
\.


--
-- Data for Name: zona_trafico; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.zona_trafico (id_zona, nombre, tipo_geometria, geometria_wkt, tipo, deleted_at) FROM stdin;
\.


--
-- Name: atractivo_id_atractivo_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.atractivo_id_atractivo_seq', 1, false);


--
-- Name: categoria_id_categoria_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.categoria_id_categoria_seq', 1, false);


--
-- Name: consulta_nsga2_id_consulta_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.consulta_nsga2_id_consulta_seq', 1, false);


--
-- Name: generacion_id_generacion_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.generacion_id_generacion_seq', 1, false);


--
-- Name: itinerario_detalle_id_detalle_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.itinerario_detalle_id_detalle_seq', 1, false);


--
-- Name: itinerario_id_itinerario_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.itinerario_id_itinerario_seq', 1, false);


--
-- Name: patron_trafico_id_patron_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.patron_trafico_id_patron_seq', 1, false);


--
-- Name: proveedor_id_proveedor_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.proveedor_id_proveedor_seq', 1, false);


--
-- Name: rol_id_rol_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.rol_id_rol_seq', 3, true);


--
-- Name: subcategoria_id_subcategoria_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.subcategoria_id_subcategoria_seq', 1, false);


--
-- Name: tipo_cambio_id_tipo_cambio_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.tipo_cambio_id_tipo_cambio_seq', 1, false);


--
-- Name: transporte_id_transporte_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.transporte_id_transporte_seq', 1, false);


--
-- Name: turista_id_turista_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.turista_id_turista_seq', 1, false);


--
-- Name: usuario_id_usuario_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.usuario_id_usuario_seq', 1, true);


--
-- Name: zona_trafico_id_zona_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.zona_trafico_id_zona_seq', 1, false);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: atractivo atractivo_nombre_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.atractivo
    ADD CONSTRAINT atractivo_nombre_key UNIQUE (nombre);


--
-- Name: atractivo atractivo_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.atractivo
    ADD CONSTRAINT atractivo_pkey PRIMARY KEY (id_atractivo);


--
-- Name: categoria categoria_nombre_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.categoria
    ADD CONSTRAINT categoria_nombre_key UNIQUE (nombre);


--
-- Name: categoria categoria_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.categoria
    ADD CONSTRAINT categoria_pkey PRIMARY KEY (id_categoria);


--
-- Name: consulta_nsga2 consulta_nsga2_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.consulta_nsga2
    ADD CONSTRAINT consulta_nsga2_pkey PRIMARY KEY (id_consulta);


--
-- Name: generacion generacion_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.generacion
    ADD CONSTRAINT generacion_pkey PRIMARY KEY (id_generacion);


--
-- Name: itinerario itinerario_codigo_confirmacion_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.itinerario
    ADD CONSTRAINT itinerario_codigo_confirmacion_key UNIQUE (codigo_confirmacion);


--
-- Name: itinerario_detalle itinerario_detalle_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.itinerario_detalle
    ADD CONSTRAINT itinerario_detalle_pkey PRIMARY KEY (id_detalle);


--
-- Name: itinerario_detalle_trafico itinerario_detalle_trafico_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.itinerario_detalle_trafico
    ADD CONSTRAINT itinerario_detalle_trafico_pkey PRIMARY KEY (id_detalle, id_patron);


--
-- Name: itinerario itinerario_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.itinerario
    ADD CONSTRAINT itinerario_pkey PRIMARY KEY (id_itinerario);


--
-- Name: patron_trafico patron_trafico_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.patron_trafico
    ADD CONSTRAINT patron_trafico_pkey PRIMARY KEY (id_patron);


--
-- Name: proveedor proveedor_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.proveedor
    ADD CONSTRAINT proveedor_pkey PRIMARY KEY (id_proveedor);


--
-- Name: rol rol_nombre_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rol
    ADD CONSTRAINT rol_nombre_key UNIQUE (nombre);


--
-- Name: rol rol_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rol
    ADD CONSTRAINT rol_pkey PRIMARY KEY (id_rol);


--
-- Name: subcategoria subcategoria_nombre_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.subcategoria
    ADD CONSTRAINT subcategoria_nombre_key UNIQUE (nombre);


--
-- Name: subcategoria subcategoria_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.subcategoria
    ADD CONSTRAINT subcategoria_pkey PRIMARY KEY (id_subcategoria);


--
-- Name: tipo_cambio tipo_cambio_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tipo_cambio
    ADD CONSTRAINT tipo_cambio_pkey PRIMARY KEY (id_tipo_cambio);


--
-- Name: transporte transporte_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transporte
    ADD CONSTRAINT transporte_pkey PRIMARY KEY (id_transporte);


--
-- Name: turista turista_id_usuario_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.turista
    ADD CONSTRAINT turista_id_usuario_key UNIQUE (id_usuario);


--
-- Name: turista turista_nro_documento_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.turista
    ADD CONSTRAINT turista_nro_documento_key UNIQUE (nro_documento);


--
-- Name: turista turista_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.turista
    ADD CONSTRAINT turista_pkey PRIMARY KEY (id_turista);


--
-- Name: usuario usuario_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuario
    ADD CONSTRAINT usuario_pkey PRIMARY KEY (id_usuario);


--
-- Name: viaje_turista viaje_turista_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.viaje_turista
    ADD CONSTRAINT viaje_turista_pkey PRIMARY KEY (id_itinerario, id_turista);


--
-- Name: zona_trafico zona_trafico_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.zona_trafico
    ADD CONSTRAINT zona_trafico_pkey PRIMARY KEY (id_zona);


--
-- Name: ix_usuario_email; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_usuario_email ON public.usuario USING btree (email);


--
-- Name: ix_usuario_reset_token; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_usuario_reset_token ON public.usuario USING btree (reset_token);


--
-- Name: atractivo atractivo_id_proveedor_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.atractivo
    ADD CONSTRAINT atractivo_id_proveedor_fkey FOREIGN KEY (id_proveedor) REFERENCES public.proveedor(id_proveedor);


--
-- Name: atractivo atractivo_id_subcategoria_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.atractivo
    ADD CONSTRAINT atractivo_id_subcategoria_fkey FOREIGN KEY (id_subcategoria) REFERENCES public.subcategoria(id_subcategoria);


--
-- Name: consulta_nsga2 consulta_nsga2_id_generacion_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.consulta_nsga2
    ADD CONSTRAINT consulta_nsga2_id_generacion_fkey FOREIGN KEY (id_generacion) REFERENCES public.generacion(id_generacion);


--
-- Name: generacion generacion_id_usuario_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.generacion
    ADD CONSTRAINT generacion_id_usuario_fkey FOREIGN KEY (id_usuario) REFERENCES public.usuario(id_usuario);


--
-- Name: itinerario_detalle itinerario_detalle_id_atractivo_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.itinerario_detalle
    ADD CONSTRAINT itinerario_detalle_id_atractivo_fkey FOREIGN KEY (id_atractivo) REFERENCES public.atractivo(id_atractivo);


--
-- Name: itinerario_detalle itinerario_detalle_id_itinerario_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.itinerario_detalle
    ADD CONSTRAINT itinerario_detalle_id_itinerario_fkey FOREIGN KEY (id_itinerario) REFERENCES public.itinerario(id_itinerario);


--
-- Name: itinerario_detalle itinerario_detalle_id_transporte_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.itinerario_detalle
    ADD CONSTRAINT itinerario_detalle_id_transporte_fkey FOREIGN KEY (id_transporte) REFERENCES public.transporte(id_transporte);


--
-- Name: itinerario_detalle_trafico itinerario_detalle_trafico_id_detalle_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.itinerario_detalle_trafico
    ADD CONSTRAINT itinerario_detalle_trafico_id_detalle_fkey FOREIGN KEY (id_detalle) REFERENCES public.itinerario_detalle(id_detalle);


--
-- Name: itinerario_detalle_trafico itinerario_detalle_trafico_id_patron_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.itinerario_detalle_trafico
    ADD CONSTRAINT itinerario_detalle_trafico_id_patron_fkey FOREIGN KEY (id_patron) REFERENCES public.patron_trafico(id_patron);


--
-- Name: itinerario itinerario_id_generacion_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.itinerario
    ADD CONSTRAINT itinerario_id_generacion_fkey FOREIGN KEY (id_generacion) REFERENCES public.generacion(id_generacion);


--
-- Name: patron_trafico patron_trafico_id_zona_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.patron_trafico
    ADD CONSTRAINT patron_trafico_id_zona_fkey FOREIGN KEY (id_zona) REFERENCES public.zona_trafico(id_zona);


--
-- Name: subcategoria subcategoria_id_categoria_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.subcategoria
    ADD CONSTRAINT subcategoria_id_categoria_fkey FOREIGN KEY (id_categoria) REFERENCES public.categoria(id_categoria);


--
-- Name: tipo_cambio tipo_cambio_id_usuario_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tipo_cambio
    ADD CONSTRAINT tipo_cambio_id_usuario_fkey FOREIGN KEY (id_usuario) REFERENCES public.usuario(id_usuario);


--
-- Name: turista turista_id_usuario_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.turista
    ADD CONSTRAINT turista_id_usuario_fkey FOREIGN KEY (id_usuario) REFERENCES public.usuario(id_usuario);


--
-- Name: usuario usuario_id_rol_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuario
    ADD CONSTRAINT usuario_id_rol_fkey FOREIGN KEY (id_rol) REFERENCES public.rol(id_rol);


--
-- Name: viaje_turista viaje_turista_id_itinerario_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.viaje_turista
    ADD CONSTRAINT viaje_turista_id_itinerario_fkey FOREIGN KEY (id_itinerario) REFERENCES public.itinerario(id_itinerario);


--
-- Name: viaje_turista viaje_turista_id_turista_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.viaje_turista
    ADD CONSTRAINT viaje_turista_id_turista_fkey FOREIGN KEY (id_turista) REFERENCES public.turista(id_turista);


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE USAGE ON SCHEMA public FROM PUBLIC;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--

\unrestrict jthRzTrbLxTvtZN6tEGEAUGf4fa61DO82tkYJidOLydeMFm1A3CxD4BJCt43dRt

