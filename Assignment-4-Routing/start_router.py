import sys
import router

def main(filename):
  config_filename = filename
  try:
    r = router.Router(config_filename)
    r.start()
  finally:
    if r: r.stop()

if __name__ == '__main__':
  if len(sys.argv) != 2:
    print 'Usage: python start_router.py config_filename'
    sys.exit(1)
  else:
    main(sys.argv[1])


