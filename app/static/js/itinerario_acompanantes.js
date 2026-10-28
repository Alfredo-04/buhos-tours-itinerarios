document.addEventListener('DOMContentLoaded', function () {
  // 1. Modales
  const elModalAcomp = document.getElementById('modalAcompanante');
  const elModalTuristas = document.getElementById('modalVerTuristas');
  const modalAcompanante = elModalAcomp ? bootstrap.Modal.getOrCreateInstance(elModalAcomp) : null;
  const modalVerTuristas = elModalTuristas ? bootstrap.Modal.getOrCreateInstance(elModalTuristas) : null;

  // Elementos UI principales
  const btnAbrirAcomp = document.getElementById('btnAbrirModalAcompanante');
  const btnAbrirTuristas = document.getElementById('btnAbrirModalTuristas');
  const formAcomp = document.getElementById('formAcompanante');
  const alertAcompErr = document.getElementById('formAcompananteError');
  const alertAcompSuc = document.getElementById('formAcompananteSuccess');
  const btnGuardarAcomp = document.getElementById('btnGuardarAcompanante');

  const inpDoc = document.getElementById('acomp_documento');
  const inpProc = document.getElementById('acomp_procedencia');
  const inpNom = document.getElementById('acomp_nombres');
  const inpApe = document.getElementById('acomp_apellidos');
  const inpEmail = document.getElementById('acomp_email');
  const inpTel = document.getElementById('acomp_telefono');

  const contenedorBanners = document.getElementById('contenedorBannersTuristas');
  const txtBtnAcompConteo = document.getElementById('txtBtnAcompConteo');
  const txtBtnTuristasConteo = document.getElementById('txtBtnTuristasConteo');

  let camposModificadosManualmente = {
    nombres: false,
    apellidos: false,
    email: false,
    telefono: false
  };

  [inpNom, inpApe, inpEmail, inpTel].forEach(inp => {
    if (inp) {
      inp.addEventListener('input', () => {
        const campo = inp.name;
        if (camposModificadosManualmente.hasOwnProperty(campo)) {
          camposModificadosManualmente[campo] = true;
        }
      });
    }
  });

  function resetearFormAcompanante() {
    if (formAcomp) formAcomp.reset();
    if (alertAcompErr) {
      alertAcompErr.textContent = '';
      alertAcompErr.classList.add('d-none');
    }
    if (alertAcompSuc) {
      alertAcompSuc.classList.add('d-none');
    }
    camposModificadosManualmente = {
      nombres: false,
      apellidos: false,
      email: false,
      telefono: false
    };
  }

  // 13.2. Botón "Añadir acompañante"
  if (btnAbrirAcomp) {
    btnAbrirAcomp.addEventListener('click', function () {
      resetearFormAcompanante();
      const idItin = btnAbrirAcomp.getAttribute('data-id-itinerario');
      if (elModalAcomp) {
        elModalAcomp.dataset.idItinerario = idItin;
      }
      if (modalAcompanante) {
        modalAcompanante.show();
      }
    });
  }

  // 13.5. Autocompletado (blur de documento o procedencia)
  async function intentarAutocompletar() {
    if (!inpDoc || !inpProc) return;
    const docVal = inpDoc.value.trim();
    const procVal = inpProc.value.trim();

    if (alertAcompErr) {
      alertAcompErr.textContent = '';
      alertAcompErr.classList.add('d-none');
    }
    if (alertAcompSuc) {
      alertAcompSuc.classList.add('d-none');
    }

    if (docVal && procVal) {
      try {
        const resp = await fetch(`/turistas/buscar?nro_documento=${encodeURIComponent(docVal)}&procedencia=${encodeURIComponent(procVal)}`);
        const data = await resp.json();

        if (data.encontrado && data.turista) {
          const t = data.turista;
          if (!camposModificadosManualmente.nombres && t.nombres && inpNom) inpNom.value = t.nombres;
          if (!camposModificadosManualmente.apellidos && t.apellidos && inpApe) inpApe.value = t.apellidos;
          if (!camposModificadosManualmente.email && t.email && inpEmail) inpEmail.value = t.email;
          if (!camposModificadosManualmente.telefono && t.telefono && inpTel) inpTel.value = t.telefono;

          if (alertAcompSuc) alertAcompSuc.classList.remove('d-none');
        } else if (data.motivo === 'conflicto_procedencia') {
          if (alertAcompErr) {
            alertAcompErr.textContent = `El documento ya está registrado con procedencia '${data.procedencia_registrada}'. Verifica el país o usa otro documento.`;
            alertAcompErr.classList.remove('d-none');
          }
        }
      } catch (err) {
        console.warn('Error en autocompletado:', err);
      }
    }
  }

  if (inpDoc) inpDoc.addEventListener('blur', intentarAutocompletar);
  if (inpProc) inpProc.addEventListener('blur', intentarAutocompletar);

  // 13.3. Validación en submit y 13.4 Respuesta POST
  if (formAcomp) {
    formAcomp.addEventListener('submit', async function (e) {
      e.preventDefault();

      if (alertAcompErr) {
        alertAcompErr.textContent = '';
        alertAcompErr.classList.add('d-none');
      }

      const nombres = (inpNom ? inpNom.value : '').trim();
      const apellidos = (inpApe ? inpApe.value : '').trim();
      const procedencia = (inpProc ? inpProc.value : '').trim();
      const doc = (inpDoc ? inpDoc.value : '').trim();
      const email = (inpEmail ? inpEmail.value : '').trim();
      const tel = (inpTel ? inpTel.value : '').trim();

      const regexTexto = /^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/;
      const regexDoc = /^[A-Za-z0-9-]+$/;
      const regexTel = /^[0-9+-\s]+$/;

      let errorMsg = '';

      if (!nombres || !apellidos) {
        errorMsg = 'Nombres y apellidos son obligatorios.';
      } else if (/[0-9]/.test(nombres + apellidos)) {
        errorMsg = 'Los nombres y apellidos no pueden contener números.';
      } else if (!procedencia) {
        errorMsg = 'La procedencia es obligatoria.';
      } else if (doc && !regexDoc.test(doc)) {
        errorMsg = 'El documento solo admite letras, números y guiones.';
      } else if (email && inpEmail && !inpEmail.checkValidity()) {
        errorMsg = 'El correo electrónico no tiene un formato válido.';
      } else if (tel && !regexTel.test(tel)) {
        errorMsg = 'El teléfono solo admite dígitos, +, espacios y guiones.';
      }

      if (errorMsg) {
        if (alertAcompErr) {
          alertAcompErr.textContent = errorMsg;
          alertAcompErr.classList.remove('d-none');
        }
        return;
      }

      const idItin = elModalAcomp ? elModalAcomp.dataset.idItinerario : null;
      if (!idItin) {
        if (alertAcompErr) {
          alertAcompErr.textContent = 'Identificador de itinerario no encontrado.';
          alertAcompErr.classList.remove('d-none');
        }
        return;
      }

      if (btnGuardarAcomp) {
        btnGuardarAcomp.disabled = true;
        btnGuardarAcomp.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Guardando...';
      }

      try {
        const resp = await fetch(`/itinerarios/${idItin}/acompanantes`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            nombres: nombres,
            apellidos: apellidos,
            procedencia: procedencia,
            nro_documento: doc || null,
            email: email || null,
            telefono: tel || null
          })
        });

        const resData = await resp.json();

        if (resp.status === 201 && resData.success) {
          if (modalAcompanante) modalAcompanante.hide();

          // Actualizar conteos en botones
          const conteoTxt = `${resData.total_registrados}/${resData.esperado}`;
          if (txtBtnAcompConteo) txtBtnAcompConteo.textContent = conteoTxt;
          if (txtBtnTuristasConteo) txtBtnTuristasConteo.textContent = conteoTxt;

          // Actualizar Banners
          if (contenedorBanners) {
            if (resData.completo) {
              contenedorBanners.innerHTML = `
                <div class="alert alert-success border-success-subtle shadow-sm d-flex align-items-center gap-2 mb-0" id="bannerCompleto">
                  <i class="bi bi-check-circle-fill fs-5"></i>
                  <div>
                    Grupo completo: <span id="txtRegistradosNum">${resData.total_registrados}</span>/${resData.esperado} personas registradas.
                  </div>
                </div>
              `;
              if (btnAbrirAcomp) btnAbrirAcomp.disabled = true;
            } else {
              contenedorBanners.innerHTML = `
                <div class="alert alert-warning border-warning-subtle shadow-sm d-flex align-items-center gap-2 mb-0" id="bannerFaltantes">
                  <i class="bi bi-exclamation-triangle-fill fs-5"></i>
                  <div>
                    Faltan <strong id="txtFaltantesNum">${resData.faltantes}</strong> persona${resData.faltantes > 1 ? 's' : ''} por registrar (<span id="txtRegistradosNum">${resData.total_registrados}</span>/${resData.esperado}).
                  </div>
                </div>
              `;
            }
          }

          alert('Acompañante añadido correctamente.');
        } else {
          const errBackend = resData.error || 'No se pudo añadir el acompañante.';
          if (alertAcompErr) {
            alertAcompErr.textContent = errBackend;
            alertAcompErr.classList.remove('d-none');
          }
        }
      } catch (err) {
        if (alertAcompErr) {
          alertAcompErr.textContent = 'Error de red o comunicación: ' + err.message;
          alertAcompErr.classList.remove('d-none');
        }
      } finally {
        if (btnGuardarAcomp) {
          btnGuardarAcomp.disabled = false;
          btnGuardarAcomp.innerHTML = 'Guardar acompañante';
        }
      }
    });
  }

  // 13.6. Botón "Ver turistas del itinerario"
  if (btnAbrirTuristas) {
    btnAbrirTuristas.addEventListener('click', async function () {
      const idItin = btnAbrirTuristas.getAttribute('data-id-itinerario');
      const headerCont = document.getElementById('modalTuristasHeader');
      const tablaCont = document.getElementById('modalTuristasContenido');

      if (modalVerTuristas) modalVerTuristas.show();

      if (tablaCont) tablaCont.innerHTML = '<div class="text-center py-4 text-muted"><span class="spinner-border spinner-border-sm me-2"></span>Cargando turistas...</div>';
      if (headerCont) headerCont.innerHTML = '';

      try {
        const resp = await fetch(`/itinerarios/${idItin}/turistas`);
        const data = await resp.json();

        if (resp.ok && data.turistas) {
          const conteo = data.conteo || {};
          if (headerCont) {
            if (conteo.completo) {
              headerCont.innerHTML = `
                <div class="alert alert-success py-2 px-3 small mb-0 d-flex align-items-center justify-content-between">
                  <span><i class="bi bi-check-circle-fill me-1"></i>Grupo completo (${conteo.total_registrados}/${conteo.esperado})</span>
                  <span class="badge bg-success">Completo</span>
                </div>
              `;
            } else {
              headerCont.innerHTML = `
                <div class="alert alert-warning py-2 px-3 small mb-0 d-flex align-items-center justify-content-between">
                  <span><i class="bi bi-exclamation-triangle-fill me-1"></i>Faltan ${conteo.faltantes} por registrar (${conteo.total_registrados}/${conteo.esperado})</span>
                  <span class="badge bg-warning text-dark">${conteo.total_registrados}/${conteo.esperado}</span>
                </div>
              `;
            }
          }

          if (tablaCont) {
            let filasHtml = '';
            data.turistas.forEach(t => {
              const esTitular = t.rol === 'titular';
              const badgeRol = esTitular
                ? '<span class="badge bg-success"><i class="bi bi-star-fill me-1"></i>Titular</span>'
                : '<span class="badge bg-secondary">Acompañante</span>';

              filasHtml += `
                <tr>
                  <td>${badgeRol}</td>
                  <td class="fw-bold">${t.nombres} ${t.apellidos}</td>
                  <td><code>${t.nro_documento || 'S/D'}</code></td>
                  <td>${t.procedencia || 'No indicada'}</td>
                  <td>${t.email || '<span class="text-muted fst-italic">--</span>'}</td>
                  <td>${t.telefono || '<span class="text-muted fst-italic">--</span>'}</td>
                </tr>
              `;
            });

            tablaCont.innerHTML = `
              <div class="table-responsive">
                <table class="table table-hover table-sm align-middle mb-0">
                  <thead class="bg-light text-muted small text-uppercase" style="font-size: 0.72rem;">
                    <tr>
                      <th style="width: 120px;">Rol</th>
                      <th>Nombre completo</th>
                      <th>Documento</th>
                      <th>Procedencia</th>
                      <th>Email</th>
                      <th>Teléfono</th>
                    </tr>
                  </thead>
                  <tbody>
                    ${filasHtml}
                  </tbody>
                </table>
              </div>
            `;
          }
        } else {
          if (tablaCont) {
            tablaCont.innerHTML = `<div class="alert alert-danger">${data.error || 'Error al obtener la lista de turistas.'}</div>`;
          }
        }
      } catch (err) {
        if (tablaCont) {
          tablaCont.innerHTML = `<div class="alert alert-danger">Error de conexión: ${err.message}</div>`;
        }
      }
    });
  }
});
