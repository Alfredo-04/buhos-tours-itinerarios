--
-- PostgreSQL database dump
--

\restrict bFSSD5TGf5hDJOFOO381HfE1UcMAPCvD6jX9UGDJ9XKZdfBgwNyZykGfzue3gbw

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
-- Name: distancia_atractivo; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.distancia_atractivo (
    id_distancia integer NOT NULL,
    id_atractivo_origen integer NOT NULL,
    id_atractivo_destino integer NOT NULL,
    distancia_km numeric(8,3) NOT NULL,
    duracion_min numeric(6,2) NOT NULL,
    fuente character varying(20) NOT NULL,
    fecha_calculo timestamp without time zone NOT NULL
);


ALTER TABLE public.distancia_atractivo OWNER TO postgres;

--
-- Name: distancia_atractivo_id_distancia_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.distancia_atractivo_id_distancia_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.distancia_atractivo_id_distancia_seq OWNER TO postgres;

--
-- Name: distancia_atractivo_id_distancia_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.distancia_atractivo_id_distancia_seq OWNED BY public.distancia_atractivo.id_distancia;


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
-- Name: distancia_atractivo id_distancia; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.distancia_atractivo ALTER COLUMN id_distancia SET DEFAULT nextval('public.distancia_atractivo_id_distancia_seq'::regclass);


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
1db495f0f1f0
\.


--
-- Data for Name: atractivo; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.atractivo (id_atractivo, nombre, descripcion, latitud, longitud, direccion, horario_apertura, horario_cierre, costo_entrada, tiempo_visita_estimado, dias_cerrado, imagen_url, fecha_inicio, fecha_fin, afecta_rutas, sensible_al_clima, tipo_clima_ideal, id_subcategoria, id_proveedor, deleted_at) FROM stdin;
1	Apacheta Mirador Jach'a Kollo	Mirador ceremonial andino con vista panorámica de 360 grados de la ciudad y el Illimani de gran importancia para ritos precolombinos.	-16.5089366	-68.1486962	Zona Villa Nuevo Potosí La Paz	00:00:00	23:59:00	0.00	30	\N	\N	\N	\N	f	t	Despejado	4	1	\N
2	Área Protegida al Bosquecillo de Auquisamaña	Área natural protegida que preserva la flora y fauna nativa del valle seco paceño ideal para senderismo suave e interpretación ecológica.	-16.5518352	-68.0712713	Final Av. Manuel Iturralde Auquisamaña La Paz	08:30:00	17:00:00	0.00	120	\N	\N	\N	\N	f	t	Soleado	6	1	\N
3	Parque Nacional de Mallasa	Extenso espacio verde recreativo metropolitano con senderos forestados áreas de camping y espacios deportivos familiares.	-16.5728897	-68.0834358	Carretera Principal a Mallasa Km 12 La Paz	08:00:00	17:00:00	5.00	90	Lunes	\N	\N	\N	f	t	Soleado	5	1	\N
4	Centro Cultural Museo San Francisco	Complejo conventual colonial barroco mestizo que exhibe arte sacro criptas históricas y acceso a los techos con vistas del centro.	-16.4961328	-68.1373270	Plaza San Francisco Av. Mariscal Santa Cruz La Paz	09:00:00	18:00:00	20.00	75	Domingo	\N	\N	\N	f	f	\N	1	3	\N
5	Bioparque Municipal Vesty Pakos	Centro de custodia de fauna silvestre nativa de los Andes y la Amazonía enfocado en educación ambiental y conservación de especies.	-16.5723125	-68.0831168	Valle de Mallasa (junto al Parque Nacional) La Paz	10:00:00	15:00:00	10.00	120	Lunes,Martes	\N	\N	\N	f	t	Soleado	6	1	\N
6	Bosquecillo de Pura Pura	El pulmón verde más grande del norte urbano cubierto de densos bosques de eucaliptos áreas recreativas y el parque ecológico municipal.	-16.4811429	-68.1560094	Av. Naciones Unidas Zona Pura Pura La Paz	09:00:00	17:00:00	2.00	90	\N	\N	\N	\N	f	t	Soleado	5	1	\N
7	Calle Jaén	La calle colonial mejor preservada de La Paz caracterizada por su calzada empedrada fachadas de colores intensos y mitos populares urbanos.	-16.4922506	-68.1359009	Calle Jaén (entre Sucre e Indaburu) Centro La Paz	00:00:00	23:59:00	0.00	45	\N	\N	\N	\N	f	f	\N	3	1	\N
8	Mercado Lanza	Punto gastronómico tradicional con menú general del día a precio fijo por persona. El plato incluye fondo a elección del menú general (chairo o ají de papa lisa o fricandó o sopa y segundo variados o api con pastel o buñuelo) más una bebida.	-16.4948598	-68.1373799	Plaza Mayor de San Francisco Centro La Paz	06:00:00	21:00:00	15.00	45	\N	\N	\N	\N	t	f	\N	9	5	\N
9	Museo Nacional de Arte	Palacio dieciochesco del Conde de Arana que resguarda obras maestras desde el barroco mestizo de Melchor Pérez de Holguín hasta arte contemporáneo.	-16.4957093	-68.1342315	Calle Comercio esq. Socabaya Plaza Murillo La Paz	09:00:00	17:00:00	20.00	90	Lunes	\N	\N	\N	f	f	\N	1	2	\N
10	Museo Nacional de Etnografía y Folklore	Palacio de los Marqueses de Villa Verde que exhibe la riqueza textil cerámica máscaras y herencia cultural indígena de Bolivia.	-16.4943462	-68.1350004	Calle Ingavi esq. Jenaro Sanjinés Centro La Paz	09:00:00	17:00:00	20.00	90	Lunes	\N	\N	\N	f	f	\N	1	2	\N
11	Casa Museo Marina Núñez del Prado	Inmueble neocolonial que resguarda la mayor colección escultórica en piedra y madera de la célebre artista indigenista boliviana.	-16.5065103	-68.1306581	Ecuador #2034 Zona Sopocachi La Paz	09:30:00	16:30:00	10.00	60	Sábado,Domingo	\N	\N	\N	f	f	\N	1	2	\N
12	Cementerio General	Necrópolis histórica que destaca por sus imponentes mausoleos patrimoniales y gigantescos murales de arte urbano contemporáneo.	-16.4965735	-68.1518147	Av. Baptista Zona Cementerio La Paz	08:00:00	16:00:00	0.00	60	\N	\N	\N	\N	t	f	\N	3	1	\N
13	Iglesia de La Merced	Templo barroco colonial del siglo XVIII poseedor de un magnífico retablo tallado cubierto en pan de oro y un destacado púlpito histórico.	-16.4968470	-68.1325336	Calle Comercio esq. Colón Centro La Paz	09:00:00	12:00:00	0.00	30	Sábado,Domingo	\N	\N	\N	f	f	\N	2	8	\N
14	Iglesia de San Agustín	Histórico templo reedificado en la época de la República que alberga un claustro tradicional y lienzos religiosos invaluables.	-16.4978426	-68.1342961	Calle Mercado esq. Ayacucho (junto a la Alcaldía) La Paz	08:30:00	11:30:00	0.00	30	Sábado,Domingo	\N	\N	\N	f	f	\N	2	8	\N
15	Iglesia de Santo Domingo	Destacada fachada barroca de piedra labrada del siglo XVIII con retablos neoclásicos y fuerte valor histórico patrimonial.	-16.4945108	-68.1344588	Calle Ingavi esq. Yanacocha Centro La Paz	09:00:00	12:00:00	0.00	30	Sábado,Domingo	\N	\N	\N	f	f	\N	2	8	\N
16	Iglesia de Nuestra Señora del Carmen	Templo de gran devoción histórica paceña ligado a los protomártires de la revolución de julio custodia valiosas imágenes religiosas.	-16.4954055	-68.1322916	Calle Ballivián esq. Colón Centro La Paz	08:30:00	12:00:00	0.00	30	Sábado,Domingo	\N	\N	\N	f	f	\N	2	8	\N
17	Las Cholas	Punto gastronómico tradicional al aire libre a precio fijo por persona. El plato incluye un sándwich de chola con opción de acompañamiento a elección del cliente más una bebida.	-16.5445391	-68.0925152	Av. Costanera esq. Calle 8 de Calacoto La Paz	09:00:00	21:00:00	19.00	45	\N	\N	\N	\N	f	t	Soleado	9	4	\N
18	Mercado de Las Brujas	Arteria comercial mística y tradicional donde se expenden hierbas medicinales amuletos fetos de llama y objetos para ofrendas a la Pachamama.	-16.4959482	-68.1389643	Calle Melchor Jiménez y Linares Centro La Paz	08:00:00	19:30:00	0.00	45	\N	\N	\N	\N	t	f	\N	8	6	\N
19	Parque Laguna de Cota Cota	Espacio verde de la Zona Sur estructurado alrededor de una hermosa laguna artificial habitada por aves cuenta con puentes y botes recreativos.	-16.5414689	-68.0645932	Calle 30 de Cota Cota Av. Muñoz Reyes La Paz	09:00:00	17:30:00	4.00	60	Lunes	\N	\N	\N	f	t	Soleado	5	1	\N
20	Mirador Killi Killi	Punto de observación urbano elevado edificado sobre un búnker prehispánico que regala la panorámica más famosa y completa del Illimani y la urbe.	-16.4952937	-68.1276252	Av. Blanca Cárdenas Zona Villa Pabón La Paz	06:00:00	22:00:00	0.00	30	\N	\N	\N	\N	f	t	Despejado	4	1	\N
21	Mirador Letrero La Paz	Punto fotográfico moderno ubicado en una de las laderas altas occidentales que exhibe el gran rótulo de identidad de la ciudad.	-16.5194339	-68.1438742	Zona Alto Següencoma / Alto Tembladerani La Paz	00:00:00	23:59:00	0.00	20	\N	\N	\N	\N	f	t	Despejado	4	1	\N
22	Muela del Diablo	Imponente formación geológica de origen volcánico con forma de colmillo gigante ideal para caminatas senderismo de aventura y vistas de los valles.	-16.5614636	-68.0564190	Comunidad de Pedregal Zona Sur La Paz	00:00:00	23:59:00	0.00	150	\N	\N	\N	\N	f	t	Despejado	6	1	\N
23	Museo de la Coca	Pequeño y didáctico repositorio privado que aborda la historia los usos rituales medicinales e impacto social de la sagrada hoja andina de coca.	-16.4974613	-68.1382715	Calle Linares #90 Centro La Paz	10:00:00	18:00:00	20.00	45	Domingo	\N	\N	\N	f	f	\N	1	7	\N
24	Museo Tambo Quirquincho	Antiguo caserón de caciques prehispánicos convertido en museo que expone colecciones de platería máscaras festivas fotos antiguas y trajes de época.	-16.4933905	-68.1380264	Plaza Alonzo de Mendoza Centro La Paz	09:00:00	17:00:00	8.00	60	Lunes	\N	\N	\N	f	f	\N	1	1	\N
25	Santuario del Señor Jesús del Gran Poder	Epicentro de la fe católica andina templo que resguarda el lienzo original de la Santísima Trinidad y eje de la mayor entrada folklórica del país.	-16.4997126	-68.1425725	Calle Antonio Gallardo Zona Chijini La Paz	08:00:00	19:00:00	0.00	30	\N	\N	\N	\N	t	f	\N	2	8	\N
26	Plaza Abaroa (Sopocachi)	Tradicional espacio público arbolado y recientemente remodelado en el corazón del barrio bohemio de Sopocachi rodeado de cafés y arte.	-16.5102149	-68.1266874	Av. 20 de Octubre entre Belisario Salinas y Pedro Salazar	00:00:00	23:59:00	0.00	30	\N	\N	\N	\N	f	t	Soleado	7	1	\N
27	Plaza Humboldt (Calacoto)	Plaza de encuentro clave en la Zona Sur que conecta el transporte tradicional de los valles y alberga ferias artesanales de fin de semana.	-16.5417003	-68.0915057	Av. Ballivián esq. Calle 13 de Calacoto La Paz	00:00:00	23:59:00	0.00	25	\N	\N	\N	\N	f	t	Soleado	7	1	\N
28	Plaza Murillo	Centro político e histórico de Bolivia (Kilómetro Cero) que congrega el Palacio Quemado el Palacio Legislativo y la imponente Catedral Metropolitana.	-16.4956695	-68.1335174	Plaza Murillo (calles Comercio Socabaya Ingavi Ballivián)	00:00:00	23:59:00	0.00	40	\N	\N	\N	\N	t	f	\N	7	1	\N
29	Plaza Riosinho	Plaza patrimonial de arquitectura colonial que marca el remate de la calle Jaén hito de la resistencia e historia revolucionaria paceña.	-16.4912973	-68.1356057	Final Calle Jaén esq. Calle Sucre Norte La Paz	00:00:00	23:59:00	0.00	20	\N	\N	\N	\N	f	t	Soleado	7	1	\N
30	Plaza San Francisco	La plaza cívica más importante del país atrio urbano masivo de encuentro social y cultural situado al pie de la monumental basílica.	-16.4955947	-68.1371254	Av. Mariscal Santa Cruz esq. Sagárnaga Centro La Paz	00:00:00	23:59:00	0.00	30	\N	\N	\N	\N	t	f	\N	7	1	\N
31	Valle de la Luna	Sorprendente laberinto geológico erosionado de pináculos arcillosos y estalagmitas desérticas que recrean un paisaje de aspecto lunar singular.	-16.5671895	-68.0939081	Carretera Principal a Mallasa (frente al club de golf) La Paz	08:00:00	17:30:00	15.00	90	\N	\N	\N	\N	f	t	Soleado	6	1	\N
\.


--
-- Data for Name: categoria; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.categoria (id_categoria, nombre, descripcion, deleted_at) FROM stdin;
1	Cultural	Repositorios históricos patrimoniales museos templos y espacios de identidad comunitaria o artística.	\N
2	Naturaleza	Áreas protegidas formaciones geológicas bofedales altoandinos miradores naturales y espacios ecológicos.	\N
3	Urbano	Plazas calles paseos peatonales y centros neurálgicos de conectividad ciudadana e hitos icónicos.	\N
4	Gastronomía	Mercados tradicionales y sectores icónicos de expendio de platos típicos de identidad paceña.	\N
\.


--
-- Data for Name: consulta_nsga2; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.consulta_nsga2 (id_consulta, fecha, id_generacion, num_atractivos, num_transportes, presupuesto, tiempo_disponible_horas, intereses, tamano_poblacion, generaciones, prob_cruce, prob_mutacion, num_soluciones, mejor_afinidad, mejor_tiempo, soluciones_viables, todas_exceden, tiempo_ejecucion_seg, convergencia, diversidad_final) FROM stdin;
\.


--
-- Data for Name: distancia_atractivo; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.distancia_atractivo (id_distancia, id_atractivo_origen, id_atractivo_destino, distancia_km, duracion_min, fuente, fecha_calculo) FROM stdin;
1	1	2	14.118	17.69	osrm	2026-10-07 16:20:29.756815
2	1	3	16.030	18.73	osrm	2026-10-07 16:20:31.908378
3	1	4	3.689	5.99	osrm	2026-10-07 16:20:33.416619
4	1	5	17.105	20.13	osrm	2026-10-07 16:20:34.53654
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
1	1	lunes	00:00:00	06:00:00	1.11	verde	trafico	\N
2	1	lunes	06:00:00	07:30:00	1.26	amarillo	trafico	\N
3	1	lunes	07:30:00	09:00:00	1.26	amarillo	trafico	\N
4	1	lunes	09:00:00	12:00:00	1.45	naranja	trafico	\N
5	1	lunes	12:00:00	14:30:00	1.75	rojo	trafico	\N
6	1	lunes	14:30:00	16:30:00	1.60	naranja	trafico	\N
7	1	lunes	16:30:00	18:30:00	1.78	rojo	trafico	\N
8	1	lunes	18:30:00	22:00:00	1.45	naranja	trafico	\N
9	1	lunes	22:00:00	23:59:00	1.26	amarillo	trafico	\N
10	1	martes	00:00:00	06:00:00	1.11	verde	trafico	\N
11	1	martes	06:00:00	07:30:00	1.26	amarillo	trafico	\N
12	1	martes	07:30:00	09:00:00	1.26	amarillo	trafico	\N
13	1	martes	09:00:00	12:00:00	1.45	naranja	trafico	\N
14	1	martes	12:00:00	14:30:00	1.75	rojo	trafico	\N
15	1	martes	14:30:00	16:30:00	1.60	naranja	trafico	\N
16	1	martes	16:30:00	18:30:00	1.78	rojo	trafico	\N
17	1	martes	18:30:00	22:00:00	1.45	naranja	trafico	\N
18	1	martes	22:00:00	23:59:00	1.26	amarillo	trafico	\N
19	1	miercoles	00:00:00	06:00:00	1.11	verde	trafico	\N
20	1	miercoles	06:00:00	07:30:00	1.26	amarillo	trafico	\N
21	1	miercoles	07:30:00	09:00:00	1.26	amarillo	trafico	\N
22	1	miercoles	09:00:00	12:00:00	1.45	naranja	trafico	\N
23	1	miercoles	12:00:00	14:30:00	1.75	rojo	trafico	\N
24	1	miercoles	14:30:00	16:30:00	1.60	naranja	trafico	\N
25	1	miercoles	16:30:00	18:30:00	1.78	rojo	trafico	\N
26	1	miercoles	18:30:00	22:00:00	1.45	naranja	trafico	\N
27	1	miercoles	22:00:00	23:59:00	1.26	amarillo	trafico	\N
28	1	jueves	00:00:00	06:00:00	1.11	verde	trafico	\N
29	1	jueves	06:00:00	07:30:00	1.26	amarillo	trafico	\N
30	1	jueves	07:30:00	09:00:00	1.26	amarillo	trafico	\N
31	1	jueves	09:00:00	12:00:00	1.45	naranja	trafico	\N
32	1	jueves	12:00:00	14:30:00	1.75	rojo	trafico	\N
33	1	jueves	14:30:00	16:30:00	1.60	naranja	trafico	\N
34	1	jueves	16:30:00	18:30:00	1.78	rojo	trafico	\N
35	1	jueves	18:30:00	22:00:00	1.45	naranja	trafico	\N
36	1	jueves	22:00:00	23:59:00	1.26	amarillo	trafico	\N
37	1	viernes	00:00:00	06:00:00	1.11	verde	trafico	\N
38	1	viernes	06:00:00	07:30:00	1.26	amarillo	trafico	\N
39	1	viernes	07:30:00	09:00:00	1.26	amarillo	trafico	\N
40	1	viernes	09:00:00	12:00:00	1.45	naranja	trafico	\N
41	1	viernes	12:00:00	14:30:00	1.75	rojo	trafico	\N
42	1	viernes	14:30:00	16:30:00	1.60	naranja	trafico	\N
43	1	viernes	16:30:00	18:30:00	1.78	rojo	trafico	\N
44	1	viernes	18:30:00	22:00:00	1.45	naranja	trafico	\N
45	1	viernes	22:00:00	23:59:00	1.26	amarillo	trafico	\N
46	1	sabado	00:00:00	06:00:00	1.11	verde	trafico	\N
47	1	sabado	06:00:00	07:30:00	1.20	amarillo	trafico	\N
48	1	sabado	07:30:00	09:00:00	1.35	amarillo	trafico	\N
49	1	sabado	09:00:00	12:00:00	1.75	rojo	trafico	\N
50	1	sabado	12:00:00	14:30:00	1.55	naranja	trafico	\N
51	1	sabado	14:30:00	16:30:00	1.60	naranja	trafico	\N
52	1	sabado	16:30:00	18:30:00	1.58	naranja	trafico	\N
53	1	sabado	18:30:00	22:00:00	1.40	naranja	trafico	\N
54	1	sabado	22:00:00	23:59:00	1.10	verde	trafico	\N
55	1	domingo	00:00:00	06:00:00	1.05	verde	trafico	\N
56	1	domingo	06:00:00	07:30:00	1.05	verde	trafico	\N
57	1	domingo	07:30:00	09:00:00	1.30	amarillo	trafico	\N
58	1	domingo	09:00:00	12:00:00	1.75	rojo	trafico	\N
59	1	domingo	12:00:00	14:30:00	1.24	amarillo	trafico	\N
60	1	domingo	14:30:00	16:30:00	1.35	amarillo	trafico	\N
61	1	domingo	16:30:00	18:30:00	1.24	amarillo	trafico	\N
62	1	domingo	18:30:00	22:00:00	1.10	verde	trafico	\N
63	1	domingo	22:00:00	23:59:00	1.05	verde	trafico	\N
64	2	lunes	00:00:00	06:00:00	1.03	verde	trafico	\N
65	2	lunes	06:00:00	07:30:00	1.08	verde	trafico	\N
66	2	lunes	07:30:00	09:00:00	1.34	amarillo	trafico	\N
67	2	lunes	09:00:00	12:00:00	1.25	amarillo	trafico	\N
68	2	lunes	12:00:00	14:30:00	1.25	amarillo	trafico	\N
69	2	lunes	14:30:00	16:30:00	1.31	amarillo	trafico	\N
70	2	lunes	16:30:00	18:30:00	1.31	amarillo	trafico	\N
71	2	lunes	18:30:00	22:00:00	1.10	verde	trafico	\N
72	2	lunes	22:00:00	23:59:00	1.03	verde	trafico	\N
73	2	martes	00:00:00	06:00:00	1.03	verde	trafico	\N
74	2	martes	06:00:00	07:30:00	1.08	verde	trafico	\N
75	2	martes	07:30:00	09:00:00	1.34	amarillo	trafico	\N
76	2	martes	09:00:00	12:00:00	1.25	amarillo	trafico	\N
77	2	martes	12:00:00	14:30:00	1.25	amarillo	trafico	\N
78	2	martes	14:30:00	16:30:00	1.31	amarillo	trafico	\N
79	2	martes	16:30:00	18:30:00	1.31	amarillo	trafico	\N
80	2	martes	18:30:00	22:00:00	1.10	verde	trafico	\N
81	2	martes	22:00:00	23:59:00	1.03	verde	trafico	\N
82	2	miercoles	00:00:00	06:00:00	1.03	verde	trafico	\N
83	2	miercoles	06:00:00	07:30:00	1.08	verde	trafico	\N
84	2	miercoles	07:30:00	09:00:00	1.34	amarillo	trafico	\N
85	2	miercoles	09:00:00	12:00:00	1.25	amarillo	trafico	\N
86	2	miercoles	12:00:00	14:30:00	1.25	amarillo	trafico	\N
87	2	miercoles	14:30:00	16:30:00	1.31	amarillo	trafico	\N
88	2	miercoles	16:30:00	18:30:00	1.31	amarillo	trafico	\N
89	2	miercoles	18:30:00	22:00:00	1.10	verde	trafico	\N
90	2	miercoles	22:00:00	23:59:00	1.03	verde	trafico	\N
91	2	jueves	00:00:00	06:00:00	1.03	verde	trafico	\N
92	2	jueves	06:00:00	07:30:00	1.08	verde	trafico	\N
93	2	jueves	07:30:00	09:00:00	1.34	amarillo	trafico	\N
94	2	jueves	09:00:00	12:00:00	1.25	amarillo	trafico	\N
95	2	jueves	12:00:00	14:30:00	1.25	amarillo	trafico	\N
96	2	jueves	14:30:00	16:30:00	1.31	amarillo	trafico	\N
97	2	jueves	16:30:00	18:30:00	1.31	amarillo	trafico	\N
98	2	jueves	18:30:00	22:00:00	1.10	verde	trafico	\N
99	2	jueves	22:00:00	23:59:00	1.03	verde	trafico	\N
100	2	viernes	00:00:00	06:00:00	1.03	verde	trafico	\N
101	2	viernes	06:00:00	07:30:00	1.08	verde	trafico	\N
102	2	viernes	07:30:00	09:00:00	1.34	amarillo	trafico	\N
103	2	viernes	09:00:00	12:00:00	1.25	amarillo	trafico	\N
104	2	viernes	12:00:00	14:30:00	1.25	amarillo	trafico	\N
105	2	viernes	14:30:00	16:30:00	1.31	amarillo	trafico	\N
106	2	viernes	16:30:00	18:30:00	1.31	amarillo	trafico	\N
107	2	viernes	18:30:00	22:00:00	1.10	verde	trafico	\N
108	2	viernes	22:00:00	23:59:00	1.03	verde	trafico	\N
109	2	sabado	00:00:00	06:00:00	1.03	verde	trafico	\N
110	2	sabado	06:00:00	07:30:00	1.08	verde	trafico	\N
111	2	sabado	07:30:00	09:00:00	1.34	amarillo	trafico	\N
112	2	sabado	09:00:00	12:00:00	1.25	amarillo	trafico	\N
113	2	sabado	12:00:00	14:30:00	1.25	amarillo	trafico	\N
114	2	sabado	14:30:00	16:30:00	1.31	amarillo	trafico	\N
115	2	sabado	16:30:00	18:30:00	1.31	amarillo	trafico	\N
116	2	sabado	18:30:00	22:00:00	1.10	verde	trafico	\N
117	2	sabado	22:00:00	23:59:00	1.03	verde	trafico	\N
118	2	domingo	00:00:00	06:00:00	1.03	verde	trafico	\N
119	2	domingo	06:00:00	07:30:00	1.08	verde	trafico	\N
120	2	domingo	07:30:00	09:00:00	1.03	verde	trafico	\N
121	2	domingo	09:00:00	12:00:00	1.05	verde	trafico	\N
122	2	domingo	12:00:00	14:30:00	1.03	verde	trafico	\N
123	2	domingo	14:30:00	16:30:00	1.03	verde	trafico	\N
124	2	domingo	16:30:00	18:30:00	1.05	verde	trafico	\N
125	2	domingo	18:30:00	22:00:00	1.03	verde	trafico	\N
126	2	domingo	22:00:00	23:59:00	1.03	verde	trafico	\N
127	3	lunes	00:00:00	06:00:00	1.00	verde	trafico	\N
128	3	lunes	06:00:00	07:30:00	1.05	verde	trafico	\N
129	3	lunes	07:30:00	09:00:00	1.43	naranja	trafico	\N
130	3	lunes	09:00:00	12:00:00	1.48	naranja	trafico	\N
131	3	lunes	12:00:00	14:30:00	1.45	naranja	trafico	\N
132	3	lunes	14:30:00	16:30:00	1.45	naranja	trafico	\N
133	3	lunes	16:30:00	18:30:00	1.50	naranja	trafico	\N
134	3	lunes	18:30:00	22:00:00	1.10	verde	trafico	\N
135	3	lunes	22:00:00	23:59:00	1.04	verde	trafico	\N
136	3	martes	00:00:00	06:00:00	1.00	verde	trafico	\N
137	3	martes	06:00:00	07:30:00	1.05	verde	trafico	\N
138	3	martes	07:30:00	09:00:00	1.43	naranja	trafico	\N
139	3	martes	09:00:00	12:00:00	1.48	naranja	trafico	\N
140	3	martes	12:00:00	14:30:00	1.45	naranja	trafico	\N
141	3	martes	14:30:00	16:30:00	1.45	naranja	trafico	\N
142	3	martes	16:30:00	18:30:00	1.50	naranja	trafico	\N
143	3	martes	18:30:00	22:00:00	1.10	verde	trafico	\N
144	3	martes	22:00:00	23:59:00	1.04	verde	trafico	\N
145	3	miercoles	00:00:00	06:00:00	1.00	verde	trafico	\N
146	3	miercoles	06:00:00	07:30:00	1.05	verde	trafico	\N
147	3	miercoles	07:30:00	09:00:00	1.43	naranja	trafico	\N
148	3	miercoles	09:00:00	12:00:00	1.48	naranja	trafico	\N
149	3	miercoles	12:00:00	14:30:00	1.45	naranja	trafico	\N
150	3	miercoles	14:30:00	16:30:00	1.45	naranja	trafico	\N
151	3	miercoles	16:30:00	18:30:00	1.50	naranja	trafico	\N
152	3	miercoles	18:30:00	22:00:00	1.10	verde	trafico	\N
153	3	miercoles	22:00:00	23:59:00	1.04	verde	trafico	\N
154	3	jueves	00:00:00	06:00:00	1.00	verde	trafico	\N
155	3	jueves	06:00:00	07:30:00	1.05	verde	trafico	\N
156	3	jueves	07:30:00	09:00:00	1.43	naranja	trafico	\N
157	3	jueves	09:00:00	12:00:00	1.48	naranja	trafico	\N
158	3	jueves	12:00:00	14:30:00	1.45	naranja	trafico	\N
159	3	jueves	14:30:00	16:30:00	1.45	naranja	trafico	\N
160	3	jueves	16:30:00	18:30:00	1.50	naranja	trafico	\N
161	3	jueves	18:30:00	22:00:00	1.10	verde	trafico	\N
162	3	jueves	22:00:00	23:59:00	1.04	verde	trafico	\N
163	3	viernes	00:00:00	06:00:00	1.00	verde	trafico	\N
164	3	viernes	06:00:00	07:30:00	1.05	verde	trafico	\N
165	3	viernes	07:30:00	09:00:00	1.43	naranja	trafico	\N
166	3	viernes	09:00:00	12:00:00	1.48	naranja	trafico	\N
167	3	viernes	12:00:00	14:30:00	1.45	naranja	trafico	\N
168	3	viernes	14:30:00	16:30:00	1.45	naranja	trafico	\N
169	3	viernes	16:30:00	18:30:00	1.50	naranja	trafico	\N
170	3	viernes	18:30:00	22:00:00	1.10	verde	trafico	\N
171	3	viernes	22:00:00	23:59:00	1.04	verde	trafico	\N
172	3	sabado	00:00:00	06:00:00	1.00	verde	trafico	\N
173	3	sabado	06:00:00	07:30:00	1.05	verde	trafico	\N
174	3	sabado	07:30:00	09:00:00	1.08	verde	trafico	\N
175	3	sabado	09:00:00	12:00:00	1.15	amarillo	trafico	\N
176	3	sabado	12:00:00	14:30:00	1.15	amarillo	trafico	\N
177	3	sabado	14:30:00	16:30:00	1.05	verde	trafico	\N
178	3	sabado	16:30:00	18:30:00	1.10	verde	trafico	\N
179	3	sabado	18:30:00	22:00:00	1.03	verde	trafico	\N
180	3	sabado	22:00:00	23:59:00	1.00	verde	trafico	\N
181	3	domingo	00:00:00	06:00:00	1.00	verde	trafico	\N
182	3	domingo	06:00:00	07:30:00	1.05	verde	trafico	\N
183	3	domingo	07:30:00	09:00:00	1.08	verde	trafico	\N
184	3	domingo	09:00:00	12:00:00	1.15	amarillo	trafico	\N
185	3	domingo	12:00:00	14:30:00	1.15	amarillo	trafico	\N
186	3	domingo	14:30:00	16:30:00	1.05	verde	trafico	\N
187	3	domingo	16:30:00	18:30:00	1.10	verde	trafico	\N
188	3	domingo	18:30:00	22:00:00	1.03	verde	trafico	\N
189	3	domingo	22:00:00	23:59:00	1.00	verde	trafico	\N
190	4	lunes	00:00:00	06:00:00	1.00	verde	trafico	\N
191	4	lunes	06:00:00	07:30:00	1.00	verde	trafico	\N
192	4	lunes	07:30:00	09:00:00	1.05	verde	trafico	\N
193	4	lunes	09:00:00	12:00:00	1.05	verde	trafico	\N
194	4	lunes	12:00:00	14:30:00	1.05	verde	trafico	\N
195	4	lunes	14:30:00	16:30:00	1.10	verde	trafico	\N
196	4	lunes	16:30:00	18:30:00	1.25	amarillo	trafico	\N
197	4	lunes	18:30:00	22:00:00	1.05	verde	trafico	\N
198	4	lunes	22:00:00	23:59:00	1.00	verde	trafico	\N
199	4	martes	00:00:00	06:00:00	1.00	verde	trafico	\N
200	4	martes	06:00:00	07:30:00	1.00	verde	trafico	\N
201	4	martes	07:30:00	09:00:00	1.05	verde	trafico	\N
202	4	martes	09:00:00	12:00:00	1.05	verde	trafico	\N
203	4	martes	12:00:00	14:30:00	1.05	verde	trafico	\N
204	4	martes	14:30:00	16:30:00	1.10	verde	trafico	\N
205	4	martes	16:30:00	18:30:00	1.25	amarillo	trafico	\N
206	4	martes	18:30:00	22:00:00	1.05	verde	trafico	\N
207	4	martes	22:00:00	23:59:00	1.00	verde	trafico	\N
208	4	miercoles	00:00:00	06:00:00	1.00	verde	trafico	\N
209	4	miercoles	06:00:00	07:30:00	1.00	verde	trafico	\N
210	4	miercoles	07:30:00	09:00:00	1.05	verde	trafico	\N
211	4	miercoles	09:00:00	12:00:00	1.05	verde	trafico	\N
212	4	miercoles	12:00:00	14:30:00	1.05	verde	trafico	\N
213	4	miercoles	14:30:00	16:30:00	1.10	verde	trafico	\N
214	4	miercoles	16:30:00	18:30:00	1.25	amarillo	trafico	\N
215	4	miercoles	18:30:00	22:00:00	1.05	verde	trafico	\N
216	4	miercoles	22:00:00	23:59:00	1.00	verde	trafico	\N
217	4	jueves	00:00:00	06:00:00	1.00	verde	trafico	\N
218	4	jueves	06:00:00	07:30:00	1.00	verde	trafico	\N
219	4	jueves	07:30:00	09:00:00	1.05	verde	trafico	\N
220	4	jueves	09:00:00	12:00:00	1.05	verde	trafico	\N
221	4	jueves	12:00:00	14:30:00	1.05	verde	trafico	\N
222	4	jueves	14:30:00	16:30:00	1.10	verde	trafico	\N
223	4	jueves	16:30:00	18:30:00	1.25	amarillo	trafico	\N
224	4	jueves	18:30:00	22:00:00	1.05	verde	trafico	\N
225	4	jueves	22:00:00	23:59:00	1.00	verde	trafico	\N
226	4	viernes	00:00:00	06:00:00	1.00	verde	trafico	\N
227	4	viernes	06:00:00	07:30:00	1.00	verde	trafico	\N
228	4	viernes	07:30:00	09:00:00	1.05	verde	trafico	\N
229	4	viernes	09:00:00	12:00:00	1.05	verde	trafico	\N
230	4	viernes	12:00:00	14:30:00	1.05	verde	trafico	\N
231	4	viernes	14:30:00	16:30:00	1.10	verde	trafico	\N
232	4	viernes	16:30:00	18:30:00	1.25	amarillo	trafico	\N
233	4	viernes	18:30:00	22:00:00	1.05	verde	trafico	\N
234	4	viernes	22:00:00	23:59:00	1.00	verde	trafico	\N
235	4	sabado	00:00:00	06:00:00	1.00	verde	trafico	\N
236	4	sabado	06:00:00	07:30:00	1.00	verde	trafico	\N
237	4	sabado	07:30:00	09:00:00	1.05	verde	trafico	\N
238	4	sabado	09:00:00	12:00:00	1.05	verde	trafico	\N
239	4	sabado	12:00:00	14:30:00	1.05	verde	trafico	\N
240	4	sabado	14:30:00	16:30:00	1.10	verde	trafico	\N
241	4	sabado	16:30:00	18:30:00	1.25	amarillo	trafico	\N
242	4	sabado	18:30:00	22:00:00	1.05	verde	trafico	\N
243	4	sabado	22:00:00	23:59:00	1.00	verde	trafico	\N
244	4	domingo	00:00:00	06:00:00	1.00	verde	trafico	\N
245	4	domingo	06:00:00	07:30:00	1.00	verde	trafico	\N
246	4	domingo	07:30:00	09:00:00	1.05	verde	trafico	\N
247	4	domingo	09:00:00	12:00:00	1.05	verde	trafico	\N
248	4	domingo	12:00:00	14:30:00	1.05	verde	trafico	\N
249	4	domingo	14:30:00	16:30:00	1.10	verde	trafico	\N
250	4	domingo	16:30:00	18:30:00	1.25	amarillo	trafico	\N
251	4	domingo	18:30:00	22:00:00	1.05	verde	trafico	\N
252	4	domingo	22:00:00	23:59:00	1.00	verde	trafico	\N
253	5	lunes	00:00:00	06:00:00	1.00	verde	trafico	\N
254	5	lunes	06:00:00	07:30:00	1.00	verde	trafico	\N
255	5	lunes	07:30:00	09:00:00	1.23	amarillo	trafico	\N
256	5	lunes	09:00:00	12:00:00	1.05	verde	trafico	\N
257	5	lunes	12:00:00	14:30:00	1.03	verde	trafico	\N
258	5	lunes	14:30:00	16:30:00	1.05	verde	trafico	\N
259	5	lunes	16:30:00	18:30:00	1.18	amarillo	trafico	\N
260	5	lunes	18:30:00	22:00:00	1.03	verde	trafico	\N
261	5	lunes	22:00:00	23:59:00	1.01	verde	trafico	\N
262	5	martes	00:00:00	06:00:00	1.00	verde	trafico	\N
263	5	martes	06:00:00	07:30:00	1.00	verde	trafico	\N
264	5	martes	07:30:00	09:00:00	1.23	amarillo	trafico	\N
265	5	martes	09:00:00	12:00:00	1.05	verde	trafico	\N
266	5	martes	12:00:00	14:30:00	1.03	verde	trafico	\N
267	5	martes	14:30:00	16:30:00	1.05	verde	trafico	\N
268	5	martes	16:30:00	18:30:00	1.18	amarillo	trafico	\N
269	5	martes	18:30:00	22:00:00	1.03	verde	trafico	\N
270	5	martes	22:00:00	23:59:00	1.01	verde	trafico	\N
271	5	miercoles	00:00:00	06:00:00	1.00	verde	trafico	\N
272	5	miercoles	06:00:00	07:30:00	1.00	verde	trafico	\N
273	5	miercoles	07:30:00	09:00:00	1.23	amarillo	trafico	\N
274	5	miercoles	09:00:00	12:00:00	1.05	verde	trafico	\N
275	5	miercoles	12:00:00	14:30:00	1.03	verde	trafico	\N
276	5	miercoles	14:30:00	16:30:00	1.05	verde	trafico	\N
277	5	miercoles	16:30:00	18:30:00	1.18	amarillo	trafico	\N
278	5	miercoles	18:30:00	22:00:00	1.03	verde	trafico	\N
279	5	miercoles	22:00:00	23:59:00	1.01	verde	trafico	\N
280	5	jueves	00:00:00	06:00:00	1.00	verde	trafico	\N
281	5	jueves	06:00:00	07:30:00	1.00	verde	trafico	\N
282	5	jueves	07:30:00	09:00:00	1.23	amarillo	trafico	\N
283	5	jueves	09:00:00	12:00:00	1.05	verde	trafico	\N
284	5	jueves	12:00:00	14:30:00	1.03	verde	trafico	\N
285	5	jueves	14:30:00	16:30:00	1.05	verde	trafico	\N
286	5	jueves	16:30:00	18:30:00	1.18	amarillo	trafico	\N
287	5	jueves	18:30:00	22:00:00	1.03	verde	trafico	\N
288	5	jueves	22:00:00	23:59:00	1.01	verde	trafico	\N
289	5	viernes	00:00:00	06:00:00	1.00	verde	trafico	\N
290	5	viernes	06:00:00	07:30:00	1.00	verde	trafico	\N
291	5	viernes	07:30:00	09:00:00	1.23	amarillo	trafico	\N
292	5	viernes	09:00:00	12:00:00	1.05	verde	trafico	\N
293	5	viernes	12:00:00	14:30:00	1.03	verde	trafico	\N
294	5	viernes	14:30:00	16:30:00	1.05	verde	trafico	\N
295	5	viernes	16:30:00	18:30:00	1.18	amarillo	trafico	\N
296	5	viernes	18:30:00	22:00:00	1.03	verde	trafico	\N
297	5	viernes	22:00:00	23:59:00	1.01	verde	trafico	\N
298	5	sabado	00:00:00	06:00:00	1.00	verde	trafico	\N
299	5	sabado	06:00:00	07:30:00	1.00	verde	trafico	\N
300	5	sabado	07:30:00	09:00:00	1.23	amarillo	trafico	\N
301	5	sabado	09:00:00	12:00:00	1.05	verde	trafico	\N
302	5	sabado	12:00:00	14:30:00	1.03	verde	trafico	\N
303	5	sabado	14:30:00	16:30:00	1.05	verde	trafico	\N
304	5	sabado	16:30:00	18:30:00	1.18	amarillo	trafico	\N
305	5	sabado	18:30:00	22:00:00	1.03	verde	trafico	\N
306	5	sabado	22:00:00	23:59:00	1.01	verde	trafico	\N
307	5	domingo	00:00:00	06:00:00	1.00	verde	trafico	\N
308	5	domingo	06:00:00	07:30:00	1.00	verde	trafico	\N
309	5	domingo	07:30:00	09:00:00	1.00	verde	trafico	\N
310	5	domingo	09:00:00	12:00:00	1.00	verde	trafico	\N
311	5	domingo	12:00:00	14:30:00	1.00	verde	trafico	\N
312	5	domingo	14:30:00	16:30:00	1.00	verde	trafico	\N
313	5	domingo	16:30:00	18:30:00	1.00	verde	trafico	\N
314	5	domingo	18:30:00	22:00:00	1.00	verde	trafico	\N
315	5	domingo	22:00:00	23:59:00	1.00	verde	trafico	\N
316	6	lunes	00:00:00	06:00:00	1.00	verde	trafico	\N
317	6	lunes	06:00:00	07:30:00	1.03	verde	trafico	\N
318	6	lunes	07:30:00	09:00:00	1.18	amarillo	trafico	\N
319	6	lunes	09:00:00	12:00:00	1.01	verde	trafico	\N
320	6	lunes	12:00:00	14:30:00	1.05	verde	trafico	\N
321	6	lunes	14:30:00	16:30:00	1.05	verde	trafico	\N
322	6	lunes	16:30:00	18:30:00	1.28	amarillo	trafico	\N
323	6	lunes	18:30:00	22:00:00	1.13	verde	trafico	\N
324	6	lunes	22:00:00	23:59:00	1.00	verde	trafico	\N
325	6	martes	00:00:00	06:00:00	1.00	verde	trafico	\N
326	6	martes	06:00:00	07:30:00	1.03	verde	trafico	\N
327	6	martes	07:30:00	09:00:00	1.18	amarillo	trafico	\N
328	6	martes	09:00:00	12:00:00	1.01	verde	trafico	\N
329	6	martes	12:00:00	14:30:00	1.05	verde	trafico	\N
330	6	martes	14:30:00	16:30:00	1.05	verde	trafico	\N
331	6	martes	16:30:00	18:30:00	1.28	amarillo	trafico	\N
332	6	martes	18:30:00	22:00:00	1.13	verde	trafico	\N
333	6	martes	22:00:00	23:59:00	1.00	verde	trafico	\N
334	6	miercoles	00:00:00	06:00:00	1.00	verde	trafico	\N
335	6	miercoles	06:00:00	07:30:00	1.03	verde	trafico	\N
336	6	miercoles	07:30:00	09:00:00	1.18	amarillo	trafico	\N
337	6	miercoles	09:00:00	12:00:00	1.01	verde	trafico	\N
338	6	miercoles	12:00:00	14:30:00	1.05	verde	trafico	\N
339	6	miercoles	14:30:00	16:30:00	1.05	verde	trafico	\N
340	6	miercoles	16:30:00	18:30:00	1.28	amarillo	trafico	\N
341	6	miercoles	18:30:00	22:00:00	1.13	verde	trafico	\N
342	6	miercoles	22:00:00	23:59:00	1.00	verde	trafico	\N
343	6	jueves	00:00:00	06:00:00	1.00	verde	trafico	\N
344	6	jueves	06:00:00	07:30:00	1.03	verde	trafico	\N
345	6	jueves	07:30:00	09:00:00	1.18	amarillo	trafico	\N
346	6	jueves	09:00:00	12:00:00	1.01	verde	trafico	\N
347	6	jueves	12:00:00	14:30:00	1.05	verde	trafico	\N
348	6	jueves	14:30:00	16:30:00	1.05	verde	trafico	\N
349	6	jueves	16:30:00	18:30:00	1.28	amarillo	trafico	\N
350	6	jueves	18:30:00	22:00:00	1.13	verde	trafico	\N
351	6	jueves	22:00:00	23:59:00	1.00	verde	trafico	\N
352	6	viernes	00:00:00	06:00:00	1.00	verde	trafico	\N
353	6	viernes	06:00:00	07:30:00	1.03	verde	trafico	\N
354	6	viernes	07:30:00	09:00:00	1.18	amarillo	trafico	\N
355	6	viernes	09:00:00	12:00:00	1.01	verde	trafico	\N
356	6	viernes	12:00:00	14:30:00	1.05	verde	trafico	\N
357	6	viernes	14:30:00	16:30:00	1.05	verde	trafico	\N
358	6	viernes	16:30:00	18:30:00	1.28	amarillo	trafico	\N
359	6	viernes	18:30:00	22:00:00	1.13	verde	trafico	\N
360	6	viernes	22:00:00	23:59:00	1.00	verde	trafico	\N
361	6	sabado	00:00:00	06:00:00	1.00	verde	trafico	\N
362	6	sabado	06:00:00	07:30:00	1.01	verde	trafico	\N
363	6	sabado	07:30:00	09:00:00	1.01	verde	trafico	\N
364	6	sabado	09:00:00	12:00:00	1.05	verde	trafico	\N
365	6	sabado	12:00:00	14:30:00	1.05	verde	trafico	\N
366	6	sabado	14:30:00	16:30:00	1.10	verde	trafico	\N
367	6	sabado	16:30:00	18:30:00	1.01	verde	trafico	\N
368	6	sabado	18:30:00	22:00:00	1.01	verde	trafico	\N
369	6	sabado	22:00:00	23:59:00	1.00	verde	trafico	\N
370	6	domingo	00:00:00	06:00:00	1.00	verde	trafico	\N
371	6	domingo	06:00:00	07:30:00	1.01	verde	trafico	\N
372	6	domingo	07:30:00	09:00:00	1.01	verde	trafico	\N
373	6	domingo	09:00:00	12:00:00	1.05	verde	trafico	\N
374	6	domingo	12:00:00	14:30:00	1.05	verde	trafico	\N
375	6	domingo	14:30:00	16:30:00	1.10	verde	trafico	\N
376	6	domingo	16:30:00	18:30:00	1.01	verde	trafico	\N
377	6	domingo	18:30:00	22:00:00	1.01	verde	trafico	\N
378	6	domingo	22:00:00	23:59:00	1.00	verde	trafico	\N
\.


--
-- Data for Name: proveedor; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.proveedor (id_proveedor, razon_social, tipo, contacto_nombre, contacto_telefono, contacto_email, tarifa_especial, observaciones, deleted_at) FROM stdin;
1	Gobierno Autónomo Municipal de La Paz (GAMLP)	Institución pública	Secretaría Culturas y Turismo	22406000	gamlp_turismo@lapaz.bo	0.00	Administrador de la mayoría de museos municipales miradores plazas y áreas protegidas urbanas.	\N
2	Fundación Cultural del Banco Central de Bolivia (FC-BCB)	Fundación estatal	Dirección Nacional MNA-MUSEF	22408600	info@fundacionculturalbcb.bo	0.00	Ente responsable del Museo Nacional de Arte y el MUSEF. Ofrece pases liberados a guías certificados.	\N
3	Santuario Basílica de San Francisco	Entidad religiosa	Administración del Convento	22315050	museosanfrancisco@gmail.com	15.00	Tarifa corporativa negociable para grupos agenciados de más de 10 personas.	\N
4	Asociación de Kioskos de Sándwiches de Chola Las Cholas	Asociación comercial	Directiva de las Caseras	\N	\N	\N	Establecimientos individuales. Se coordina el consumo directo con cada casera por volumen.	\N
5	Asociación de Vendedoras del Mercado Lanza	Asociación gremial	Secretaría General de Conflictos	\N	\N	\N	Nexo directo para desayunos o refrigerios grupales tradicionales.	\N
6	Asociación Gremial del Mercado de las Brujas	Asociación artesanal	Representante de Amautas y Artesanos	\N	\N	\N	Coordinación de respeto y permisos fotográficos grupales con los yatiris y amautas locales.	\N
7	Museo de la Coca (Privado)	Empresa privada	Administración General	22311998	info@cocamuseum.com	10.00	Tarifa reducida exclusiva para agencias aliadas con flujos semanales.	\N
8	Arzobispado de La Paz	Institución religiosa	Cancillería del Arzobispado	22406115	info@arzobispadolapaz.org	0.00	Administra los templos e iglesias históricas del centro.	\N
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
1	Museos	Espacios cerrados dedicados a la exhibición resguardo y conservación de patrimonio arqueológico artístico e histórico.	1	\N
2	Iglesias y Templos	Lugares sagrados y conventos de arquitectura colonial y republicana de alto valor artístico e histórico.	1	\N
3	Sitios Patrimoniales y Calles Históricas	Arterias viales urbanas y conjuntos arquitectónicos antiguos conservados con identidad tradicional.	1	\N
4	Miradores	Puntos geográficos altos acondicionados para la observación panorámica y contextualización urbana o natural.	2	\N
5	Parques y Bosquecillos	Espacios naturales delimitados destinados a la conservación ecológica recreación y avistamiento de fauna.	2	\N
6	Áreas Protegidas	Zonas de conservación ambiental flora y fauna protegidas y formaciones geológicas de valor singular.	2	\N
7	Plazas	Espacios públicos abiertos y nodos urbanos decorados con hitos históricos o escultóricos de alta afluencia.	3	\N
8	Mercados Tradicionales	Centrales de abasto populares organizadas en sectores tradicionales de comercio de artesanías y mística.	3	\N
9	Gastronomía Tradicional	Puntos de expendio y sectores dedicados exclusivamente a la comida típica y patrimonio culinario paceño.	4	\N
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
1	Taxi	Privado	4	06:00:00	23:00:00	150.00	por_dia	25.00	\N
2	Van Ejecutiva (HiAce/H-1)	Privado	10	06:00:00	22:00:00	400.00	por_dia	25.00	\N
3	Minibús Ejecutivo (Sprinter)	Privado	22	06:00:00	22:00:00	700.00	por_dia	20.00	\N
4	Caminata	Público	30	06:00:00	22:00:00	0.00	por_persona	4.50	\N
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
1	uyustus_tumusla	poligono	POLYGON ((-68.1488006 -16.493196,-68.147739 -16.4962038,-68.1447527 -16.4966483,-68.1446223 -16.4988375,-68.1416852 -16.4978456,-68.1392776 -16.4964699,-68.1404581 -16.4936497,-68.1433961 -16.4930471,-68.1443388 -16.4893541,-68.1446861 -16.4892631,-68.1440211 -16.4921145,-68.1455987 -16.4926214,-68.1488006 -16.493196))	trafico	\N
2	terminal_buses	poligono	POLYGON ((-68.1447172 -16.4890554,-68.1442113 -16.4892274,-68.1390958 -16.4915493,-68.1375367 -16.4928956,-68.1370156 -16.492618,-68.1390178 -16.4910242,-68.1401751 -16.487933,-68.144675 -16.4883211,-68.1447172 -16.4890554))	trafico	\N
3	centro_politico	poligono	POLYGON ((-68.1366672 -16.4960836,-68.1341986 -16.4925908,-68.1302543 -16.4950953,-68.1333177 -16.499684,-68.1356514 -16.4981003,-68.1366672 -16.4960836))	trafico	\N
4	miraflores_triangular	poligono	POLYGON ((-68.1215883 -16.5039433,-68.1230848 -16.5014543,-68.1209904 -16.501342,-68.1188557 -16.5012547,-68.12064573564007 -16.50497317726769,-68.1201299 -16.5059125,-68.1203316 -16.5060052,-68.1215883 -16.5039433))	trafico	\N
5	av_6_agosto_prado	poligono	POLYGON ((-68.1309858 -16.503555,-68.1335233 -16.5001964,-68.1340311 -16.5006251,-68.1314155 -16.5039195,-68.1316 -16.5042629,-68.1282751 -16.5071609,-68.1241129 -16.5114373,-68.1238855 -16.5113359,-68.1309858 -16.503555))	trafico	\N
6	calacoto_san_miguel	poligono	POLYGON ((-68.0929493 -16.5459734,-68.0943173 -16.5417725,-68.0825178 -16.5385055,-68.0779032 -16.5387669,-68.0761301 -16.5470305,-68.076615 -16.5469831,-68.0782588 -16.5391483,-68.0825297 -16.5389254,-68.0935513 -16.5420414,-68.0920582 -16.5456929,-68.0929493 -16.5459734))	trafico	\N
\.


--
-- Name: atractivo_id_atractivo_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.atractivo_id_atractivo_seq', 31, true);


--
-- Name: categoria_id_categoria_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.categoria_id_categoria_seq', 4, true);


--
-- Name: consulta_nsga2_id_consulta_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.consulta_nsga2_id_consulta_seq', 1, false);


--
-- Name: distancia_atractivo_id_distancia_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.distancia_atractivo_id_distancia_seq', 4, true);


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

SELECT pg_catalog.setval('public.patron_trafico_id_patron_seq', 378, true);


--
-- Name: proveedor_id_proveedor_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.proveedor_id_proveedor_seq', 8, true);


--
-- Name: rol_id_rol_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.rol_id_rol_seq', 3, true);


--
-- Name: subcategoria_id_subcategoria_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.subcategoria_id_subcategoria_seq', 9, true);


--
-- Name: tipo_cambio_id_tipo_cambio_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.tipo_cambio_id_tipo_cambio_seq', 1, false);


--
-- Name: transporte_id_transporte_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.transporte_id_transporte_seq', 4, true);


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

SELECT pg_catalog.setval('public.zona_trafico_id_zona_seq', 6, true);


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
-- Name: distancia_atractivo distancia_atractivo_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.distancia_atractivo
    ADD CONSTRAINT distancia_atractivo_pkey PRIMARY KEY (id_distancia);


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
-- Name: distancia_atractivo uq_distancia_origen_destino; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.distancia_atractivo
    ADD CONSTRAINT uq_distancia_origen_destino UNIQUE (id_atractivo_origen, id_atractivo_destino);


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
-- Name: distancia_atractivo distancia_atractivo_id_atractivo_destino_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.distancia_atractivo
    ADD CONSTRAINT distancia_atractivo_id_atractivo_destino_fkey FOREIGN KEY (id_atractivo_destino) REFERENCES public.atractivo(id_atractivo);


--
-- Name: distancia_atractivo distancia_atractivo_id_atractivo_origen_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.distancia_atractivo
    ADD CONSTRAINT distancia_atractivo_id_atractivo_origen_fkey FOREIGN KEY (id_atractivo_origen) REFERENCES public.atractivo(id_atractivo);


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

\unrestrict bFSSD5TGf5hDJOFOO381HfE1UcMAPCvD6jX9UGDJ9XKZdfBgwNyZykGfzue3gbw

